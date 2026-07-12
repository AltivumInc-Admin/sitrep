"""One conversational turn of the Game Plan OS agent.

Stateless per invocation: history is loaded from DynamoDB, replayed into the
Agent as prior messages, and the new exchange is appended after the turn.
Only plain text is persisted - tool-use blocks are an implementation detail
of a single turn and replaying them partially would produce invalid
conversations.
"""
import datetime
import json
from zoneinfo import ZoneInfo

from strands import Agent
from strands.models import BedrockModel

from agent import tools
from agent.guards import claims_change_without_tool, clean_reply
from common import config, db
from prompts import agent_prompt

HISTORY_LIMIT = 20  # messages (10 exchanges) replayed as context

# Appended to the live message only (models weight the current turn far
# above the system prompt); the raw text is what goes to history. See
# agent/guards.py for why this exists.
TURN_REMINDER = (
    "\n\n[System check: if this asks for a change, call the matching tool "
    "now, in this turn. With no tool call, nothing changed and you must say "
    "so plainly.]")


def run_turn(channel: str, message: str) -> dict:
    """Run one user message through the agent. Returns
    {reply, tools_used, mutated}."""
    now = datetime.datetime.now(ZoneInfo(config.LOCAL_TZ))
    history = db.get_chat(channel)[-HISTORY_LIMIT:]
    agent = Agent(
        model=BedrockModel(
            model_id=config.NOVA_PRO_MODEL_ID,
            temperature=0.2,
            max_tokens=900,
            streaming=False,
        ),
        system_prompt=agent_prompt.build_system(
            today=now.date().isoformat(),
            weekday=now.strftime("%A"),
            local_now=now.strftime("%H:%M"),
            tz=config.LOCAL_TZ,
        ),
        messages=[{"role": m["role"], "content": [{"text": m["text"]}]}
                  for m in history],
        tools=tools.ALL_TOOLS,
        callback_handler=None,  # no streaming printer inside Lambda
    )
    result = agent(message + TURN_REMINDER)
    reply = clean_reply(str(result)) or "(no reply)"
    used = sorted(getattr(result.metrics, "tool_metrics", {}) or {})
    if claims_change_without_tool(reply, used):
        # The agent object carries this turn's conversation, so a second call
        # is a correction inside the same exchange, not a fresh start.
        print(json.dumps({"event": "agent_claim_without_tool",
                          "channel": channel, "reply_head": reply[:120]}))
        result = agent(
            "You reported a change but called no tool, so nothing changed. "
            "Call the correct tool for my request now, then report what "
            "actually happened.")
        reply = clean_reply(str(result)) or reply
        used = sorted(getattr(result.metrics, "tool_metrics", {}) or {})
    db.append_chat(channel, message, reply)
    print(json.dumps({"event": "agent_turn", "channel": channel,
                      "tools_used": used,
                      "usage": getattr(result.metrics, "accumulated_usage", None),
                      "history_len": len(history)}))
    return {"reply": reply, "tools_used": used,
            "mutated": bool(set(used) & tools.MUTATING_TOOLS)}
