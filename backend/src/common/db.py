"""DynamoDB single-table access layer.

Table design (PK = USER#<id> for everything; SK discriminates entity type):

  PK              SK                     Entity
  --------------  ---------------------  ---------------------------------
  USER#primary    TASK#<ulid>            A task (from brain dump or manual)
  USER#primary    SITREP#<yyyy-mm-dd>    The generated daily operations order
  USER#primary    DEBRIEF#<yyyy-mm-dd>   Evening debrief answers + analysis
  USER#primary    PREF#profile           Single doc: learned preferences list

Task item shape:
  {id, title, notes, project, status: open|done|dropped,
   due: iso-date|null, created_at,
   triage: {urgency: 1-5, impact: 1-5, effort_hours, rationale}}

Preference doc shape:
  {preferences: [{text, source, learned_at, confidence}], updated_at}
"""
import datetime
import uuid

import boto3
from boto3.dynamodb.conditions import Key

from common import config

_table = boto3.resource("dynamodb").Table(config.TABLE_NAME)
_PK = f"USER#{config.USER_ID}"


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# ---------- tasks ----------

def put_task(task: dict) -> dict:
    task.setdefault("id", uuid.uuid4().hex[:12])
    task.setdefault("status", "open")
    task.setdefault("created_at", _now())
    item = {"PK": _PK, "SK": f"TASK#{task['id']}", **task}
    _table.put_item(Item=item)
    return task


def list_tasks(status: str | None = None) -> list[dict]:
    resp = _table.query(KeyConditionExpression=Key("PK").eq(_PK) & Key("SK").begins_with("TASK#"))
    items = resp.get("Items", [])
    if status:
        items = [i for i in items if i.get("status") == status]
    for i in items:
        i.pop("PK", None); i.pop("SK", None)
    return sorted(items, key=lambda i: i.get("created_at", ""), reverse=True)


def update_task(task_id: str, fields: dict) -> None:
    allowed = {k: v for k, v in fields.items()
               if k in {"title", "notes", "project", "status", "due", "triage"}}
    if not allowed:
        return
    expr = ", ".join(f"#f{i} = :v{i}" for i in range(len(allowed)))
    names = {f"#f{i}": k for i, k in enumerate(allowed)}
    values = {f":v{i}": v for i, v in enumerate(allowed.values())}
    _table.update_item(
        Key={"PK": _PK, "SK": f"TASK#{task_id}"},
        UpdateExpression=f"SET {expr}",
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
    )


# ---------- sitreps ----------

def put_sitrep(date: str, body: dict) -> None:
    _table.put_item(Item={"PK": _PK, "SK": f"SITREP#{date}", "date": date,
                          "body": body, "created_at": _now()})


def get_sitrep(date: str) -> dict | None:
    resp = _table.get_item(Key={"PK": _PK, "SK": f"SITREP#{date}"})
    return resp.get("Item")


def latest_sitrep() -> dict | None:
    resp = _table.query(
        KeyConditionExpression=Key("PK").eq(_PK) & Key("SK").begins_with("SITREP#"),
        ScanIndexForward=False, Limit=1)
    items = resp.get("Items", [])
    return items[0] if items else None


# ---------- debriefs ----------

def put_debrief(date: str, answers: dict, analysis: dict) -> None:
    _table.put_item(Item={"PK": _PK, "SK": f"DEBRIEF#{date}", "date": date,
                          "answers": answers, "analysis": analysis, "created_at": _now()})


def recent_debriefs(limit: int = 5) -> list[dict]:
    resp = _table.query(
        KeyConditionExpression=Key("PK").eq(_PK) & Key("SK").begins_with("DEBRIEF#"),
        ScanIndexForward=False, Limit=limit)
    return resp.get("Items", [])


# ---------- preferences ----------

def get_preferences() -> list[dict]:
    resp = _table.get_item(Key={"PK": _PK, "SK": "PREF#profile"})
    return resp.get("Item", {}).get("preferences", [])


def append_preferences(new_prefs: list[dict]) -> None:
    prefs = get_preferences()
    existing = {p["text"] for p in prefs}
    for p in new_prefs:
        if p["text"] not in existing:
            p.setdefault("learned_at", _now())
            prefs.append(p)
    # keep the most recent 40 to bound prompt size
    prefs = prefs[-40:]
    _table.put_item(Item={"PK": _PK, "SK": "PREF#profile",
                          "preferences": prefs, "updated_at": _now()})
