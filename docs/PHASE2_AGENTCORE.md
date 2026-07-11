# Phase 2 — AgentCore Migration (the influence play)

**Do not start this until the article is published and qualifies.** Phase 1
alone passes all three gates. Phase 2 is what makes the article the reference
piece — the AgentCore harness went GA on June 17, 2026 and community content
on it is nearly nonexistent. An honest migration writeup ("I moved my personal
agent from hand-rolled Lambda orchestration to the managed harness — here is
what broke and what got better") is first-mover territory.

Sources to cite in the article:
- Harness GA: https://aws.amazon.com/about-aws/whats-new/2026/06/amazon-bedrock-agentcore-harness-generally-available/
- New AgentCore capabilities (knowledge, optimization, guardrails):
  https://aws.amazon.com/blogs/machine-learning/new-in-amazon-bedrock-agentcore-build-agents-with-broader-knowledge-and-continuous-learning/

## What migrates, concretely

| Phase 1 (hand-rolled) | Phase 2 (AgentCore) |
|---|---|
| `common/service.py` orchestration in Lambda | Harness config: model + tools + instructions, managed loop |
| `PREF#profile` doc in DynamoDB | AgentCore **Memory** — user-preference + episodic strategies |
| Task CRUD called in-process | Task API wrapped as MCP tools via AgentCore **Gateway** |
| CloudWatch print debugging | AgentCore **Observability** traces (screenshot for the article) |
| Nothing | Session isolation, managed identity, evaluations |

## Migration steps

1. **Wrap the task store as tools.** Point AgentCore Gateway at the existing
   HTTP API (or the Lambda directly) to expose `list_tasks`, `update_task`,
   `get_recent_debriefs` as MCP tools. The DynamoDB layer does not change.
2. **Define the agent in harness config**: model (Nova Pro), the system prompt
   from `prompts/sitrep_prompt.py` as instructions, the Gateway tools, and
   memory enabled. The five-paragraph doctrine moves verbatim — the prompt IS
   the portable asset.
3. **Memory strategies**: enable user-preference extraction on debrief
   conversations; the harness replaces the hand-rolled high-confidence
   preference filter. Keep the DynamoDB PREF doc as a read-only fallback so
   Phase 1 keeps working during the cutover.
4. **Rewire the two entry points.** The scheduled Lambda and the
   `/sitrep/generate` route become thin invokers of the harness agent instead
   of calling `service.generate_sitrep()` directly. Keep the old code path
   behind an env flag (`USE_AGENTCORE=1`) so rollback is a redeploy, not a
   rewrite.
5. **Screenshot everything**: harness config, a trace in Observability showing
   the tool calls, the memory records it extracts. These images carry the
   article update.

## Honest risk register

- **Three-week-old GA.** Expect sharp edges: console/CDK/docs drift, region
  gaps (assume us-east-1 first), IAM policies that need hand-tuning.
- **Not Free Tier.** AgentCore bills through Bedrock infrastructure rates —
  explicitly acceptable per the project owner. Note it in the article; the
  challenge encourages but does not require Free Tier.
- **Timebox: 2 hours to first successful harness invocation.** If you are not
  invoking the agent by then, execute the fallback and write about why —
  friction reports about brand-new services are exactly what other builders
  need, and the article gets better, not worse.

## Fallback: Strands Agents SDK (still AWS-native, near-zero risk)

```python
# pip install strands-agents  (verify current package name/API before use)
from strands import Agent, tool

@tool
def list_open_tasks() -> list:
    """Return all open tasks with triage scores."""
    from common import db
    return db.list_tasks("open")

@tool
def recent_debriefs() -> list:
    """Return the last five evening debriefs."""
    from common import db
    return db.recent_debriefs(5)

agent = Agent(
    model="us.amazon.nova-pro-v1:0",
    system_prompt=SITREP_SYSTEM,     # from prompts/sitrep_prompt.py
    tools=[list_open_tasks, recent_debriefs],
)
result = agent("Produce today's SITREP as JSON per the schema.")
```

Runs inside the existing Lambda, no new infrastructure, and the article can
still honestly say "agentic tool-use with AWS's open-source Strands SDK."

## Article update after migration

Add a section: **"Part 2 — Moving to AgentCore harness"** with the config
snippet, one Observability screenshot, one Memory screenshot, and a frank
paragraph on friction vs. payoff. Update before the Sunday 1:00 PM PT deadline
so the judged artifact includes it.
