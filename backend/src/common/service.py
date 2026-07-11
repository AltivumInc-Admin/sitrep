"""Core orchestration: generate the game plan, triage dumps, process debriefs, email."""
import datetime
from zoneinfo import ZoneInfo

import boto3

from common import bedrock, config, db
from prompts import debrief_prompt, sitrep_prompt, triage_prompt

_ses = boto3.client("ses")


def _local_now() -> datetime.datetime:
    return datetime.datetime.now(ZoneInfo(config.LOCAL_TZ))


def triage_dump(dump: str) -> list[dict]:
    """Brain dump -> discrete triaged tasks, persisted."""
    now = _local_now()
    known_projects = sorted({t.get("project") for t in db.list_tasks("open") if t.get("project")})
    result = bedrock.converse_json(
        config.NOVA_LITE_MODEL_ID,
        triage_prompt.SYSTEM,
        triage_prompt.build_user_prompt(
            dump, f"{now.date().isoformat()} ({now.strftime('%A')})", known_projects),
        max_tokens=2000, temperature=0.2)
    created = []
    for t in result.get("tasks", []):
        created.append(db.put_task(t))
    return created


def generate_sitrep(for_date: str | None = None) -> dict:
    """Generate (or regenerate) the operations order for a date."""
    now = _local_now()
    today = for_date or now.date().isoformat()
    yesterday = (datetime.date.fromisoformat(today) - datetime.timedelta(days=1)).isoformat()

    body = bedrock.converse_json(
        config.NOVA_PRO_MODEL_ID,
        sitrep_prompt.SYSTEM,
        sitrep_prompt.build_user_prompt(
            today=today,
            weekday=now.strftime("%A"),
            local_now=now.strftime("%H:%M"),
            open_tasks=db.list_tasks("open"),
            preferences=[p for p in db.get_preferences()],
            recent_debriefs=db.recent_debriefs(5),
            yesterday_sitrep=db.get_sitrep(yesterday),
        ),
        max_tokens=3500, temperature=0.4)
    body["date"] = today
    db.put_sitrep(today, body)
    return body


def process_debrief(answers: dict) -> dict:
    """Evening loop: analyze answers, update tasks, persist learned preferences."""
    today = _local_now().date().isoformat()
    sitrep = db.get_sitrep(today) or db.latest_sitrep() or {}
    analysis = bedrock.converse_json(
        config.NOVA_PRO_MODEL_ID,
        debrief_prompt.SYSTEM,
        debrief_prompt.build_user_prompt(
            today=today,
            sitrep_body=sitrep.get("body", {}),
            answers=answers,
            recent_debriefs=db.recent_debriefs(5),
        ),
        max_tokens=2500, temperature=0.3)

    for upd in analysis.get("task_updates", []):
        if upd.get("task_id") and upd.get("status") in ("done", "dropped"):
            db.update_task(upd["task_id"], {"status": upd["status"]})

    high_conf = [
        {"text": p["text"], "source": p.get("evidence", ""), "confidence": "high"}
        for p in analysis.get("candidate_preferences", [])
        if p.get("confidence") == "high"
    ]
    if high_conf:
        db.append_preferences(high_conf)

    db.put_debrief(today, answers, analysis)
    return analysis


# ---------- email rendering ----------

def render_email_text(body: dict) -> str:
    """Plaintext rendering of the order. Terse by design."""
    ex = body.get("execution", {})
    cs = body.get("command_signal", {})
    lines = [
        f"GAME PLAN {body.get('date')}",
        "(in the spirit of a five-paragraph operations order)",
        "",
        "1. SITUATION",
        body.get("situation", {}).get("overview", ""),
        *[f"  - {c}" for c in body.get("situation", {}).get("changes_since_yesterday", [])],
        "",
        "2. MISSION",
        body.get("mission", {}).get("statement", ""),
        f"   Why: {body.get('mission', {}).get('why_decisive', '')}",
        "",
        "3. EXECUTION",
        *[f"  {b.get('start')}-{b.get('end')}  {b.get('label')} — {b.get('intent')}"
          for b in ex.get("time_blocks", [])],
        "",
        "  P1: " + "; ".join(p.get("title", "") for p in ex.get("priorities", {}).get("p1", [])),
        "  P2: " + "; ".join(p.get("title", "") for p in ex.get("priorities", {}).get("p2", [])),
        "  P3: " + "; ".join(p.get("title", "") for p in ex.get("priorities", {}).get("p3", [])),
        "  DROPPED: " + "; ".join(f"{d.get('title')} ({d.get('reason')})"
                                   for d in ex.get("deliberately_dropped", [])),
        "",
        "4. SUSTAINMENT",
        body.get("sustainment", {}).get("energy_plan", ""),
        *[f"  - {b}" for b in body.get("sustainment", {}).get("breaks", [])],
        "",
        "5. COMMAND & SIGNAL",
        *[f"  DP: {d}" for d in cs.get("decision_points", [])],
        *[f"  BLOCKER: {b}" for b in cs.get("blockers_to_escalate", [])],
        *[f"  SAY NO TO: {s}" for s in cs.get("say_no_to", [])],
    ]
    warning = cs.get("overcommitment_warning")
    if warning and str(warning).lower() != "null":
        lines += ["", f"  !! OVERCOMMITMENT: {warning}"]
    lines += ["", "-- Evening debrief questions --",
              *[f"  {i+1}. {q}" for i, q in enumerate(body.get("debrief_questions", []))]]
    return "\n".join(lines)


def send_sitrep_email(body: dict) -> None:
    _ses.send_email(
        Source=config.NOTIFY_EMAIL,
        Destination={"ToAddresses": [config.NOTIFY_EMAIL]},
        Message={
            "Subject": {"Data": f"Game Plan {body.get('date')} — {body.get('mission', {}).get('statement', '')[:80]}"},
            "Body": {"Text": {"Data": render_email_text(body)}},
        },
    )
