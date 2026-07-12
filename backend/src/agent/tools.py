"""Agent tools - thin wrappers over the existing service layer.

Every tool here is a product verb that already exists behind the REST API;
the agent adds no new capabilities, only a conversational doorway. Tools
return compact JSON strings (small token footprint) or a plain error message
the model can relay.

This module imports strands, so only import it inside code paths that run on
the function with the dependencies layer attached (the API function).
"""
import datetime
import json
from zoneinfo import ZoneInfo

from botocore.exceptions import ClientError
from strands import tool

from common import config, db, service

# Tools that change state; the API reports these so the UI knows to refresh.
MUTATING_TOOLS = {"add_tasks", "complete_task", "reopen_task", "drop_task",
                  "mark_block", "replan_day", "generate_plan"}


def _today() -> str:
    return datetime.datetime.now(ZoneInfo(config.LOCAL_TZ)).date().isoformat()


def _task_line(t: dict) -> dict:
    tr = t.get("triage") or {}
    return {"id": t.get("id"), "title": t.get("title"),
            "project": t.get("project"), "due": t.get("due"),
            "status": t.get("status"),
            "urgency": tr.get("urgency"), "impact": tr.get("impact"),
            "effort_hours": tr.get("effort_hours")}


def _plan_summary(item: dict) -> dict:
    body = item.get("body") or {}
    ex = body.get("execution") or {}
    statuses = {str(k): v for k, v in (item.get("block_status") or {}).items()}
    blocks = []
    for i, b in enumerate(ex.get("time_blocks") or []):
        if isinstance(b, dict):
            blocks.append({"index": i, "start": b.get("start"), "end": b.get("end"),
                           "label": b.get("label"), "intent": b.get("intent"),
                           "status": statuses.get(str(i))})
    prios = ex.get("priorities") or {}
    return {
        "date": item.get("date"),
        "revision": item.get("revision", 0),
        "mission": (body.get("mission") or {}).get("statement"),
        "time_blocks": blocks,
        "priorities": {tier: [{"task_id": p.get("task_id"), "title": p.get("title")}
                              for p in prios.get(tier) or [] if isinstance(p, dict)]
                       for tier in ("p1", "p2", "p3")},
        "deliberately_dropped": [{"title": d.get("title"), "reason": d.get("reason")}
                                 for d in ex.get("deliberately_dropped") or []
                                 if isinstance(d, dict)],
        "overcommitment_warning": (body.get("command_signal") or {}).get("overcommitment_warning"),
    }


def _set_status(task_id: str, status: str, verb: str) -> str:
    tasks = {t["id"]: t for t in db.list_tasks()}
    if task_id not in tasks:
        return f"Error: no task with id {task_id!r}. Use list_tasks to get real ids."
    try:
        db.update_task(task_id, {"status": status})
    except (ValueError, ClientError) as exc:
        return f"Error: {exc}"
    return json.dumps({verb: {"id": task_id, "title": tasks[task_id].get("title")}})


@tool
def get_plan() -> str:
    """Read today's game plan: mission, time blocks (with index and done/skipped
    status), ranked priorities, deliberately dropped items, and any
    overcommitment warning. Falls back to the most recent plan if none exists
    today. Always call this before discussing or changing the day."""
    item = db.get_sitrep(_today()) or db.latest_sitrep()
    if item is None:
        return json.dumps({"plan": None, "note": "no plan exists yet; offer generate_plan"})
    return json.dumps(_plan_summary(item))


@tool
def list_tasks(status: str = "open") -> str:
    """List tasks in the pool with their real ids.

    Args:
        status: one of open, done, dropped (default open)
    """
    if status not in db.TASK_STATUSES:
        return f"Error: status must be one of {sorted(db.TASK_STATUSES)}"
    return json.dumps({"tasks": [_task_line(t) for t in db.list_tasks(status)]})


@tool
def add_tasks(text: str) -> str:
    """Turn the user's report of new work into tasks in the pool. Pass their
    words close to verbatim; a triage model splits them into discrete tasks
    and scores urgency, impact, and effort.

    Args:
        text: what the user said needs doing, in their words
    """
    created = service.triage_dump(text)
    return json.dumps({"created": [_task_line(t) for t in created]})


@tool
def complete_task(task_id: str) -> str:
    """Mark one task done. Only on explicit evidence the user finished it.

    Args:
        task_id: the task's id, taken from list_tasks or get_plan
    """
    return _set_status(task_id, "done", "completed")


@tool
def reopen_task(task_id: str) -> str:
    """Reopen a task that was wrongly marked done or dropped.

    Args:
        task_id: the task's id
    """
    return _set_status(task_id, "open", "reopened")


@tool
def drop_task(task_id: str) -> str:
    """Drop a task the user explicitly no longer wants (kept in history,
    excluded from future plans). Not for deferring - open tasks the plan
    omits are already deferred.

    Args:
        task_id: the task's id
    """
    return _set_status(task_id, "dropped", "dropped")


@tool
def mark_block(index: int, status: str) -> str:
    """Record how a time block on today's plan actually went.

    Args:
        index: the block's index from get_plan
        status: done, skipped, or clear (to remove a wrong mark)
    """
    try:
        statuses = db.set_block_status(
            _today(), index, None if status == "clear" else status)
    except ValueError as exc:
        return f"Error: {exc}"
    return json.dumps({"block_status": statuses})


@tool
def replan_day(note: str) -> str:
    """Renegotiate the rest of today: the mission and finished morning stay
    pinned, everything after the current time is rebuilt around the user's
    report. Use when reality diverged from the plan - something ran long,
    finished early, or a new demand landed.

    Args:
        note: the user's report of what changed, close to verbatim
    """
    try:
        result = service.replan_sitrep(note)
    except ValueError as exc:
        return f"Error: {exc}"
    summary = _plan_summary({"body": result, "date": result.get("date"),
                             "revision": result.get("revision"),
                             "block_status": result.get("block_status")})
    return json.dumps(summary)


@tool
def generate_plan() -> str:
    """Build today's game plan from scratch (open tasks, learned preferences,
    recent debriefs). Use only when no plan exists today or the user asks for
    a full rebuild; for mid-day changes use replan_day instead."""
    body = service.generate_sitrep()
    return json.dumps(_plan_summary({"body": body, "date": body.get("date"),
                                     "revision": 0, "block_status": {}}))


@tool
def list_preferences() -> str:
    """Read what the system has learned about how the user works (from evening
    debriefs). Useful when the user asks what you know about them."""
    return json.dumps({"preferences": [
        {"text": p.get("text"), "learned_at": p.get("learned_at")}
        for p in db.get_preferences()]})


ALL_TOOLS = [get_plan, list_tasks, add_tasks, complete_task, reopen_task,
             drop_task, mark_block, replan_day, generate_plan, list_preferences]
