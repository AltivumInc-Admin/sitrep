"""Evening debrief analysis prompt (Nova Pro).

This is the learning loop — the thing that separates SITREP from a prompt
wrapper. Input: today's order + the principal's three answers. Output:
an honest after-action analysis plus candidate preference updates that will
shape every future SITREP.
"""
import json

SYSTEM = """You are conducting a personal after-action review. You compare the
plan (this morning's SITREP) against reality (the principal's debrief answers)
and extract durable lessons. Rules:
1. Be honest, not kind. If the mission was not accomplished, say so and name
   the proximate cause from the evidence given.
2. Distinguish one-off events (a surprise call) from patterns (three debriefs
   in a row show morning blocks slipping). Only patterns become preferences.
3. A preference is a short imperative usable by tomorrow's planner, e.g.
   "Never schedule deep work after 15:00 — three debriefs show it slips" or
   "Estimates on Elo tasks run 2x long; pad them".
4. confidence is "high" only when supported by at least two independent
   signals across debriefs. Low-confidence hunches stay out of the profile.
5. task_updates: mark tasks the answers say were completed (done) or
   consciously abandoned (dropped). Only include tasks you are sure about.
Respond with ONLY valid JSON."""


def build_user_prompt(*, today: str, sitrep_body: dict, answers: dict,
                      recent_debriefs: list[dict]) -> str:
    schema = {
        "summary": "2-3 sentence honest after-action summary",
        "mission_accomplished": True,
        "what_worked": ["..."],
        "what_slipped": [{"item": "...", "proximate_cause": "..."}],
        "candidate_preferences": [
            {"text": "imperative for tomorrow's planner",
             "evidence": "which debriefs/signals support it",
             "confidence": "high|medium|low"}
        ],
        "task_updates": [{"task_id": "id", "status": "done|dropped"}],
        "tomorrow_note": "one sentence the planner should read first tomorrow",
    }
    history = json.dumps(
        [{"date": d.get("date"), "answers": d.get("answers")} for d in recent_debriefs],
        default=str)
    return f"""DATE: {today}

THIS MORNING'S SITREP (the plan):
{json.dumps(sitrep_body, default=str)}

PRINCIPAL'S DEBRIEF ANSWERS (the reality):
{json.dumps(answers, default=str)}

PRIOR DEBRIEFS (for pattern detection):
{history}

OUTPUT: a single JSON object with exactly this schema:
{json.dumps(schema, indent=2)}"""
