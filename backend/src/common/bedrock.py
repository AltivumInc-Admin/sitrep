"""Thin wrapper around the Bedrock Converse API.

Two models, two jobs:
  - Nova Pro  -> SITREP generation + debrief analysis (reasoning-heavy)
  - Nova Lite -> brain-dump triage (fast, cheap, structured extraction)

All calls request JSON output and are parsed defensively: models sometimes
wrap JSON in markdown fences; strip_json() handles that.
"""
import json
import re

import boto3

from common import config

_client = boto3.client("bedrock-runtime")


def converse(model_id: str, system: str, user: str,
             max_tokens: int = 3000, temperature: float = 0.4) -> str:
    """Single-turn Converse call. Returns raw model text."""
    resp = _client.converse(
        modelId=model_id,
        system=[{"text": system}],
        messages=[{"role": "user", "content": [{"text": user}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": temperature},
    )
    return resp["output"]["message"]["content"][0]["text"]


def strip_json(text: str) -> dict:
    """Extract the first JSON object from model output, tolerating md fences."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else text
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object in model output: {text[:400]}")
    return json.loads(candidate[start:end + 1])


def converse_json(model_id: str, system: str, user: str,
                  max_tokens: int = 3000, temperature: float = 0.4,
                  retries: int = 1) -> dict:
    """Converse call that must return JSON. One retry with a stern reminder."""
    text = converse(model_id, system, user, max_tokens, temperature)
    try:
        return strip_json(text)
    except (ValueError, json.JSONDecodeError):
        if retries <= 0:
            raise
        reminder = user + "\n\nREMINDER: Respond with ONLY a valid JSON object. No prose, no markdown fences."
        return converse_json(model_id, system, reminder, max_tokens, 0.2, retries - 1)
