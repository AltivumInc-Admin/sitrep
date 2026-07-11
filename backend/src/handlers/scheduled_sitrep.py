"""EventBridge Scheduler target — 0530 local, every day.

Generates the day's operations order and delivers it by email. Failures are
raised so they land in CloudWatch and the Lambda error metric.
"""
from common import service


def handler(_event, _context):
    body = service.generate_sitrep()
    service.send_sitrep_email(body)
    return {"date": body.get("date"),
            "mission": body.get("mission", {}).get("statement")}
