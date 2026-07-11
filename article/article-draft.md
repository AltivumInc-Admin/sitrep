# Weekend Productivity Challenge: SITREP — An AI Operations Officer That Plans Your Day Like a Mission

<!-- Builder Center tag: #productivity -->
<!-- Target 900–1,200 words. [TODO] blocks are yours; everything else is editable draft. -->

## Vision & What the App Does

In Special Forces, we never started a day without an operations order. Not a
to-do list — an order: a single mission, a scheme of maneuver, a named reserve,
and the decision points where the plan was allowed to change. A to-do list is
inventory. An order is a decision.

When I left the military and started running companies, I kept the discipline
and lost the format. My task load lives across three ventures, a nonprofit, a
podcast, and a community — and like most founders, my failure mode isn't
laziness. It's the opposite: seven "priorities," a calendar scheduled to 110%,
and no one with the authority to tell me what to drop.

So I built SITREP: a personal AI operations officer. It's not a chatbot you
have to remember to talk to. It runs on a battle rhythm:

- **Throughout the day**, I brain-dump everything into one box — half-formed,
  unstructured, exactly as it arrives. A fast model triages the dump into
  discrete tasks, each scored for urgency, impact, and honest effort.
- **Every morning at 0530**, a reasoning model reads my open tasks, my recent
  debriefs, and everything it has learned about how I actually work, and
  issues the day's operations order in the military five-paragraph format:
  **Situation** (the terrain, what changed overnight), **Mission** (one
  sentence, one objective, measurable by end of day), **Execution**
  (time blocks with intent, priorities ranked P1–P3, and — critically — what
  gets *deliberately dropped*, with reasons), **Sustainment** (energy, breaks),
  and **Command & Signal** (decision points, blockers, and what to say no to
  today). It lands in my inbox and on a dashboard.
- **Every evening**, it debriefs me: three questions generated from that
  morning's actual order, never generic. An after-action review compares plan
  to reality, names what slipped and why, and — when a pattern shows up across
  multiple debriefs — writes a preference into my profile. "Estimates on
  writing tasks run 2x long; pad them." Tomorrow's order is built on it.

The doctrine is opinionated by design: one mission only, never more than 70%
of working hours scheduled (unallocated time is the reserve — friction always
comes), and an explicit overcommitment warning when the week's load is not
achievable. If SITREP is a term you know from NATO doctrine or from Call of
Duty, either one works — it means the same thing: here is the situation,
here is what we do about it.

## How I Built It

[TODO: 2–3 sentences on your actual Friday/Saturday timeline — when you
started, when the first order generated, what you did in parallel.]

The build ran backend-first, and the key decisions were mostly about what
*not* to build:

**One decision per model.** Nova Pro handles the two reasoning-heavy jobs —
the morning order and the evening after-action review. Nova Lite handles
triage, because classifying a brain dump is extraction, not judgment, and I
wanted dumping to be so cheap I'd never hesitate. Both run through Bedrock's
Converse API with strict JSON schemas and a single stern retry when a model
gets creative with markdown fences.

**The prompt is the product.** Most of my development time went into the
system prompt's doctrine rules, not infrastructure. The difference between
"here are your tasks organized nicely" and an order with teeth — a real
mission, real drops, a warning that the week is overcommitted — is entirely
in those rules. [TODO: one concrete before/after example of a prompt rule you
tuned, e.g. what the output looked like before rule 5 vs. after.]

**The learning loop earns the word "agent."** The debrief analysis
distinguishes one-off events from patterns, and only patterns supported by at
least two independent signals get persisted as preferences. Anything less
confident stays out of the profile. Without that filter, the agent learns
noise; with it, watching my own work patterns accumulate in a DynamoDB
document is genuinely uncomfortable in the way good feedback is.

**Deliberate cuts.** No Cognito, no calendar integration, no multi-user —
a shared-secret header guards a single-principal tool. Every one of those
features was a schedule risk with zero payoff for a weekend challenge.

Challenges: [TODO: be honest — the 2–3 real snags. Candidates: JSON-mode
discipline with Nova, SES identity verification ordering, EventBridge
Scheduler timezone cron, DynamoDB Decimal serialization.]

## AWS Services Used / Architecture Overview

![Architecture diagram](TODO-upload-rendered-architecture.png)

| Service | Role |
|---|---|
| **Amazon Bedrock (Nova Pro + Nova Lite)** | The operations officer: order generation, after-action analysis (Pro); brain-dump triage (Lite) |
| **AWS Lambda (Python 3.13)** | Two functions: API router and the scheduled morning brief |
| **Amazon API Gateway (HTTP API)** | REST surface for dump / tasks / generate / debrief |
| **Amazon DynamoDB** | Single table: `TASK#`, `SITREP#`, `DEBRIEF#`, `PREF#` — the whole system state |
| **Amazon EventBridge Scheduler** | Timezone-aware cron: 0530 America/Chicago, every day |
| **Amazon SES** | Delivers the morning order to my inbox |
| **AWS Amplify Hosting** | Serves the React dashboard |

The flow: brain dumps hit API Gateway → Lambda → Nova Lite → DynamoDB. At
0530, EventBridge Scheduler wakes the brief Lambda, which assembles context
(open tasks, preferences, five most recent debriefs, yesterday's order),
calls Nova Pro, persists the order, and mails it via SES. The evening debrief
runs the same path in reverse: answers → Nova Pro after-action → task status
updates and high-confidence preferences back into DynamoDB.

Everything except Bedrock usage beyond the trial sits comfortably in the Free
Tier for a single user: pay-per-request DynamoDB, two small Lambdas, one
scheduled event a day, one email a day.

## What I Learned

[TODO: keep the 3–4 that were actually true for you; delete the rest.]

- **Converse API JSON discipline.** Schema-in-prompt plus a defensive parser
  and one low-temperature retry turned out to be more reliable than I
  expected — and cheaper than tool-calling for pure-JSON workloads.
- **EventBridge Scheduler's timezone-aware cron** eliminates the classic
  UTC-offset bug entirely. `cron(30 5 * * ? *)` in `America/Chicago` just
  works, DST included.
- **Model-to-job matching is a product decision, not a cost hack.** Triage on
  Nova Lite isn't just cheaper; its speed changes user behavior — dumping
  becomes frictionless, which means the reasoning model sees more complete
  context every morning.
- **An opinionated prompt beats a capable model with a polite one.** The same
  model, same context, produces either a summary or an order depending
  entirely on whether the doctrine rules give it permission to be decisive.
- [TODO if Phase 2 attempted: one honest paragraph on AgentCore harness —
  what the config-defined agent replaced, what broke, whether Memory's
  preference extraction beat the hand-rolled filter.]

## Link to App & Repo

- **Repo:** [TODO: public GitHub URL]
- **Live app:** [TODO: Amplify URL — or state "personal single-user tool; see
  the 60-second walkthrough below" and embed the video]
- [TODO: 3–4 screenshots: the Brief view with a real order, the SITREP email,
  the debrief's "what the agent learned about you" panel, DynamoDB items]

---

*Built solo over the July 10–13 weekend for the AWS Builder Center
Productivity Challenge. The five-paragraph order format has survived a century
of contact with reality; it turns out it survives contact with a founder's
task list too.*
