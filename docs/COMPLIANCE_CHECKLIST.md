# Compliance Checklist — run line-by-line BEFORE publishing

The challenge is pass/fail. One miss forfeits the jacket regardless of speed.

## Gate 1 — Completeness

- [ ] Article is **500+ words** (count it; aim 900–1,200)
- [ ] Title starts exactly: **"Weekend Productivity Challenge: Game Plan OS — …"**
- [ ] Tag **#productivity** added on Builder Center
- [ ] Section: Vision & What the App Does (problem, purpose, user-perspective walkthrough)
- [ ] Section: How You Built It (process, key decisions, challenges + how overcome)
- [ ] Section: AWS Services Used / Architecture Overview (list + diagram)
- [ ] Section: What You Learned (skills/services/approaches discovered)
- [ ] Section: Link to App or Repo — **link tested in an incognito window**
- [ ] Published between July 10, 9:00 AM PT and July 13, 1:00 PM PT

## Gate 2 — Relevance & Functionality

- [ ] It is an **AI-powered** productivity tool (Bedrock Nova calls are core, not garnish)
- [ ] Working functionality demonstrated: screenshots AND (live URL OR 60-sec video)
- [ ] The demo shows the full loop: dump → triage → game plan → debrief → learned preference

## Gate 3 — AWS Service Usage

- [ ] At least one AWS service used (we use seven: Bedrock, Lambda, API Gateway,
      DynamoDB, EventBridge Scheduler, SES, Amplify Hosting)
- [ ] Each service's role is **explicitly described** in the architecture section

## Repo hygiene (if the repo is the "working link")

- [ ] Repo is **public**
- [ ] README explains what it is and how to deploy (already written)
- [ ] No secrets committed: no ApiKey values, no account IDs in samconfig.toml
      (add `samconfig.toml` to .gitignore or scrub it)
- [ ] Screenshots in the README or article show it actually running

## Account & profile

- [ ] builder.aws.com profile exists and is complete (prize notification goes
      to its registered email)
- [ ] 18+ ✓, T&Cs read ✓
