"""Telegram delivery channel - stdlib only (urllib), no SDK.

Used by the API function (webhook replies) and the morning-brief function
(proactive 0530 push), so it must import cleanly without the agent
dependencies layer.
"""
import json
import urllib.error
import urllib.request

from common import config

MAX_MESSAGE_CHARS = 4096  # Telegram hard limit per sendMessage
CHUNK_TARGET = 3900       # split target, leaving headroom


def configured() -> bool:
    return bool(config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID)


def chunk_text(text: str, limit: int = CHUNK_TARGET) -> list[str]:
    """Split text into <=limit chunks, preferring newline boundaries."""
    text = (text or "").strip()
    if not text:
        return []
    chunks = []
    while len(text) > limit:
        cut = text.rfind("\n", 1, limit)
        if cut == -1:
            cut = limit
        chunks.append(text[:cut].rstrip())
        text = text[cut:].lstrip("\n")
    if text:
        chunks.append(text)
    return chunks


def parse_update(update) -> dict | None:
    """Extract what the webhook handler needs from a Telegram update.
    None for updates we do not handle (edits, stickers, joins, ...)."""
    if not isinstance(update, dict):
        return None
    msg = update.get("message")
    if not isinstance(msg, dict):
        return None
    text = msg.get("text")
    chat_id = (msg.get("chat") or {}).get("id")
    if not isinstance(text, str) or not text.strip() or chat_id is None:
        return None
    return {"update_id": update.get("update_id"),
            "chat_id": str(chat_id), "text": text.strip()}


def send_message(chat_id: str, text: str) -> None:
    """Send text to a chat, chunked to Telegram's message-size limit."""
    for chunk in chunk_text(text):
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
            data=json.dumps({"chat_id": chat_id, "text": chunk}).encode("utf-8"),
            headers={"content-type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp.read()
        except urllib.error.HTTPError as exc:
            # Never let the token near a log line; the API path is enough.
            detail = exc.read()[:200].decode("utf-8", "replace")
            raise RuntimeError(f"telegram sendMessage failed: {exc.code} {detail}") from exc


def push_brief(rendered_text: str) -> bool:
    """Proactive morning push. True if sent, False if channel unconfigured."""
    if not configured():
        return False
    send_message(config.TELEGRAM_CHAT_ID, rendered_text)
    return True
