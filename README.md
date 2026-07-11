# SITREP — An AI Operations Officer That Plans Your Day Like a Mission

Every morning at 0530, SITREP reads your open tasks, your learned preferences,
and your recent evening debriefs — and issues a military five-paragraph daily
operations order: **Situation, Mission, Execution, Sustainment, Command &
Signal.** One decisive mission. Explicit drops. Never more than 70% of your
hours scheduled. Every evening it debriefs you with three questions about the
day's actual order, runs an after-action review, and persists what it learned
about how you really work — so tomorrow's order is smarter than today's.

Built for the AWS Builder Center **Build a Productivity App Weekend Challenge**
(July 10–13, 2026).

## Why an operations order instead of a to-do list

A to-do list is inventory. An operations order is a decision. The five-paragraph
format has survived a century of contact with reality because it forces three
things most productivity tools politely avoid: a single mission (not seven
priorities), explicit resource allocation (time blocks with intent, not hopes),
and a named reserve (unscheduled time, because friction always comes). The
evening debrief closes the loop — the after-action review is where the agent
earns the word "agent."

## Architecture

```
Brain dump ──▶ API GW ──▶ Lambda ──▶ Nova Lite (triage) ──▶ DynamoDB
                                                              │
EventBridge Scheduler (0530 CT) ──▶ Lambda ──▶ Nova Pro ◀─────┤
                                        │   (5-para order)    │
                                        ├──▶ SES (email)      │
                                        └──▶ DynamoDB ◀───────┘
Evening debrief ──▶ Lambda ──▶ Nova Pro (after-action) ──▶ preferences
React + Vite on Amplify Hosting ──▶ everything above
```

Full diagram: `article/architecture.mmd`.

| Layer | Service |
|---|---|
| Reasoning | Amazon Bedrock — Nova Pro (order + after-action), Nova Lite (triage) |
| Compute | AWS Lambda (Python 3.13) |
| API | Amazon API Gateway (HTTP API) |
| Data | Amazon DynamoDB (single table) |
| Cadence | Amazon EventBridge Scheduler (timezone-aware cron) |
| Delivery | Amazon SES |
| Frontend | AWS Amplify Hosting (React + Vite) |

## Quick start

See `docs/DEPLOYMENT.md` for the full walkthrough. Short version:

```bash
# 1. Verify your SES identity (one-time, requires clicking an email link)
aws ses verify-email-identity --email-address you@example.com

# 2. Deploy the backend
sam build && sam deploy --guided

# 3. Run the frontend
cd frontend && npm i
echo "VITE_API_URL=<ApiUrl output>" > .env.local
npm run dev
```

## Repo map

```
template.yaml              SAM: 2 Lambdas, DynamoDB, HTTP API, Scheduler
backend/src/
  common/                  config, bedrock wrapper, DynamoDB layer, orchestration
  handlers/                api.py (router), scheduled_sitrep.py (0530 cron)
  prompts/                 the actual product: sitrep, triage, debrief prompts
frontend/                  React + Vite, three views: Brief / Tasks / Debrief
article/                   Builder Center article draft + architecture diagram
docs/                      deployment, Phase-2 AgentCore plan, compliance checklist
CLAUDE.md                  operating brief for the coding agent
```

## Phase 2 — AgentCore

The weekend plan migrates orchestration to the newly-GA Amazon Bedrock
AgentCore harness (config-defined agent, managed memory, observability) once
the entry qualifies. Plan and fallback: `docs/PHASE2_AGENTCORE.md`.
