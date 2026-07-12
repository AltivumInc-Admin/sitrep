"""EventBridge Scheduler target — 0530 local, every day.

Generates the day's game plan and delivers it by email. Idempotent under
Scheduler/Lambda retries: if today's plan already exists (e.g. only the SES
send failed last attempt), it is reused instead of paying for a second
generation. Failures are raised so they land in CloudWatch, the Lambda error
metric, and the failure alarm.
"""
import json
import traceback

from common import db, service, telegram


def handler(_event, _context):
    today = service._local_now().date().isoformat()
    existing = db.get_sitrep(today)
    if existing:
        body = existing["body"]
        print(json.dumps({"event": "morning_brief_reusing_plan", "date": today}))
    else:
        body = service.generate_sitrep()
    service.send_sitrep_email(body)
    # Telegram is an auxiliary channel: a push failure must not error the
    # invocation, because the retry would re-send the email.
    try:
        if telegram.push_brief(service.render_email_text(body)):
            print(json.dumps({"event": "morning_brief_telegram_pushed", "date": today}))
    except Exception:
        traceback.print_exc()
        print(json.dumps({"event": "telegram_push_failed", "date": today}))
    print(json.dumps({"event": "morning_brief_delivered", "date": today,
                      "mission": body.get("mission", {}).get("statement")}))
    return {"date": today, "mission": body.get("mission", {}).get("statement")}
