"""EventBridge Scheduler target — 0530 local, every day, for every user.

Fans out across the Cognito user pool: each user's plan is generated inside
their own data partition and delivered to their email. Idempotent under
Scheduler/Lambda retries: a user whose plan already exists today is reused
instead of paying for a second generation, so a partial failure can retry
the whole fan-out safely.

Failure posture: one user's failure must not starve the rest, but any
failure must still raise at the end so it lands in CloudWatch, the Lambda
error metric, and the failure alarm. SES sandbox rejections (unverified
recipients) are logged and skipped, not failures - the send starts working
the moment production access is granted.
"""
import json
import traceback

import boto3

from common import config, db, service, telegram


def _pool_users() -> list[dict]:
    """[{sub, email}] for every confirmed user in the pool. Falls back to the
    single owner when no pool is configured (tests, minimal deploys)."""
    if not config.COGNITO_POOL_ID:
        return [{"sub": config.USER_ID, "email": config.NOTIFY_EMAIL}]
    client = boto3.client("cognito-idp")
    users, token = [], None
    while True:
        kwargs = {"UserPoolId": config.COGNITO_POOL_ID, "Limit": 60}
        if token:
            kwargs["PaginationToken"] = token
        resp = client.list_users(**kwargs)
        for u in resp.get("Users", []):
            if u.get("UserStatus") not in ("CONFIRMED", "FORCE_CHANGE_PASSWORD"):
                continue
            attrs = {a["Name"]: a["Value"] for a in u.get("Attributes", [])}
            if attrs.get("sub"):
                users.append({"sub": attrs["sub"], "email": attrs.get("email", "")})
        token = resp.get("PaginationToken")
        if not token:
            return users


def _brief_one(user: dict, today: str) -> str:
    """Generate-or-reuse and deliver one user's brief. Returns an outcome
    label for the summary log."""
    db.set_request_user(user["sub"])
    existing = db.get_sitrep(today)
    if existing:
        body = existing["body"]
    elif db.list_tasks("open") or db.latest_sitrep():
        body = service.generate_sitrep()
    else:
        return "skipped_empty_account"
    try:
        if user["email"]:
            service.send_sitrep_email(body, to=user["email"])
    except Exception as exc:
        # SES sandbox rejects unverified recipients; that is expected until
        # production access. The plan still exists in the console.
        print(json.dumps({"event": "brief_email_rejected", "user": user["sub"],
                          "error": str(exc)[:200]}))
        return "generated_email_rejected"
    # The Telegram channel is owner-only until per-user linking ships.
    if user["sub"] == config.USER_ID:
        try:
            if telegram.push_brief(service.render_email_text(body)):
                print(json.dumps({"event": "morning_brief_telegram_pushed",
                                  "date": today}))
        except Exception:
            traceback.print_exc()
            print(json.dumps({"event": "telegram_push_failed", "date": today}))
    return "delivered"


def handler(_event, _context):
    today = service._local_now().date().isoformat()
    outcomes, failures = {}, []
    for user in _pool_users():
        try:
            outcomes[user["sub"]] = _brief_one(user, today)
        except Exception as exc:
            traceback.print_exc()
            failures.append(user["sub"])
            outcomes[user["sub"]] = f"failed: {str(exc)[:120]}"
        finally:
            db.set_request_user(None)
    print(json.dumps({"event": "morning_brief_fanout", "date": today,
                      "outcomes": outcomes}))
    if failures:
        raise RuntimeError(f"morning brief failed for {len(failures)} user(s): {failures}")
    return {"date": today, "users": len(outcomes)}
