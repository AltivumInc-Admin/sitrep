"""HTTP API router — single Lambda behind API Gateway HTTP API.

Auth: shared secret in x-sitrep-key header (personal tool; deliberately no
Cognito for the weekend — see docs/DEPLOYMENT.md for the reasoning).

Routes:
  POST  /dump               {text}            -> triage brain dump into tasks
  GET   /tasks?status=open                    -> list tasks
  POST  /tasks              {title,...}       -> create one task directly
  PATCH /tasks/{id}         {status,...}      -> update task
  POST  /sitrep/generate                      -> generate today's order on demand
  GET   /sitrep/latest                        -> most recent order
  GET   /sitrep/{date}                        -> order for a date (YYYY-MM-DD)
  POST  /debrief            {answers:{q1,q2,q3}} -> run evening after-action loop
  GET   /health                               -> unauthenticated liveness check
"""
import decimal
import json
import traceback

from common import config, db, service


class _Encoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o) if o % 1 else int(o)
        return super().default(o)


def _resp(status: int, body) -> dict:
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json",
                    "access-control-allow-origin": "*",
                    "access-control-allow-headers": "content-type,x-sitrep-key",
                    "access-control-allow-methods": "GET,POST,PATCH,OPTIONS"},
        "body": json.dumps(body, cls=_Encoder, default=str),
    }


def handler(event, _context):
    http = event.get("requestContext", {}).get("http", {})
    method = http.get("method", "")
    path = event.get("rawPath", "").rstrip("/")
    if method == "OPTIONS":
        return _resp(200, {})
    if path == "/health":
        return _resp(200, {"ok": True})

    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    if headers.get("x-sitrep-key") != config.API_KEY:
        return _resp(401, {"error": "missing or invalid x-sitrep-key"})

    body = {}
    if event.get("body"):
        try:
            body = json.loads(event["body"])
        except json.JSONDecodeError:
            return _resp(400, {"error": "invalid JSON body"})
    qs = event.get("queryStringParameters") or {}

    try:
        # ---- routing ----
        if method == "POST" and path == "/dump":
            text = (body.get("text") or "").strip()
            if not text:
                return _resp(400, {"error": "text is required"})
            return _resp(200, {"created": service.triage_dump(text)})

        if method == "GET" and path == "/tasks":
            return _resp(200, {"tasks": db.list_tasks(qs.get("status"))})

        if method == "POST" and path == "/tasks":
            if not body.get("title"):
                return _resp(400, {"error": "title is required"})
            return _resp(200, {"task": db.put_task(body)})

        if method == "PATCH" and path.startswith("/tasks/"):
            db.update_task(path.split("/")[-1], body)
            return _resp(200, {"ok": True})

        if method == "POST" and path == "/sitrep/generate":
            return _resp(200, {"sitrep": service.generate_sitrep()})

        if method == "GET" and path == "/sitrep/latest":
            item = db.latest_sitrep()
            return _resp(200, {"sitrep": item})

        if method == "GET" and path.startswith("/sitrep/"):
            return _resp(200, {"sitrep": db.get_sitrep(path.split("/")[-1])})

        if method == "POST" and path == "/debrief":
            answers = body.get("answers") or {}
            if not answers:
                return _resp(400, {"error": "answers is required"})
            return _resp(200, {"analysis": service.process_debrief(answers)})

        return _resp(404, {"error": f"no route for {method} {path}"})

    except Exception as exc:  # surface real errors during the weekend build
        traceback.print_exc()
        return _resp(500, {"error": str(exc)})
