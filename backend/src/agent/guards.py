"""Pure guard helpers for the agent runtime - importable without strands,
so the test suite can cover them locally.

Nova Pro reliably pattern-completes "has been dropped" from conversation
context instead of calling the tool (observed live, twice). These guards are
the deterministic half of the defense; the prompt rules are the other half.
"""
import re

CLAIM_RE = re.compile(
    r"\b(dropped|added|marked|closed|reopened|replanned|updated|removed|"
    r"completed|scheduled|cleared)\b", re.IGNORECASE)


def claims_change_without_tool(reply: str, tools_used: list) -> bool:
    """True when the reply asserts a state change but no tool ran."""
    return not tools_used and bool(CLAIM_RE.search(reply))


def clean_reply(text: str) -> str:
    """Strip Nova's <thinking> scratchpad, which leaks into text output
    despite prompt instructions (observed live on the first deploy)."""
    text = re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL)
    # An unclosed tag swallows the rest of the reply; keep what follows it.
    text = re.sub(r"</?thinking>", "", text)
    return text.strip()
