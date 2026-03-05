# Release Roadmap

This roadmap outlines the staged delivery plan for the AI visibility product, including milestone scope, acceptance criteria, and demo readiness checks.

## Milestone 1 (1-2 weeks): Architecture, data model, mock adapters, basic dashboard

### Scope
- Finalize system architecture and key component boundaries.
- Define core data model for projects, prompts, provider responses, and scores.
- Implement mock provider adapters for local development and deterministic testing.
- Deliver a basic dashboard showing recent runs and high-level visibility metrics.

### Acceptance criteria
- Architecture document is up to date and reflects implemented component boundaries.
- Database schema (or canonical model definitions) supports:
  - Workspace/project ownership
  - Prompt/run tracking
  - Provider response storage
  - Versioned scoring output
- At least two mock adapters conform to the shared adapter interface and pass adapter contract tests.
- Dashboard can:
  - List recent runs
  - Show status per provider
  - Display a simple aggregate score card
- A new developer can run the app locally end-to-end using mocks in under 15 minutes via documented setup.

---

## Milestone 2 (2-3 weeks): Live adapters (where feasible), scoring v1, onboarding

### Scope
- Add live provider adapters for supported external providers where API access is feasible.
- Ship scoring v1 (baseline ranking/scoring logic) with explainability notes.
- Create onboarding flow for first workspace/project and initial scan.

### Acceptance criteria
- Live adapters are implemented for target providers with:
  - Config-driven enable/disable
  - Credential validation
  - Robust timeout/retry behavior
- Scoring v1 produces consistent, reproducible scores for the same inputs.
- Score output includes component-level breakdown (e.g., presence, rank, sentiment/relevance).
- Onboarding flow allows a new user to:
  - Create workspace/project
  - Connect at least one provider
  - Run first scan and view results
- Failures in one provider do not block completion of the overall scan job.

---

## Milestone 3 (1-2 weeks): Benchmarking, exports, reliability hardening

### Scope
- Add benchmarking workflows against saved baselines and prior runs.
- Implement export capabilities for results and score history.
- Harden reliability across jobs, retries, observability, and error reporting.

### Acceptance criteria
- Benchmark view can compare current run vs. baseline and prior period deltas.
- Export supports at least CSV and JSON for run-level and keyword-level results.
- Long-running scans are resumable or safely retryable without duplicate writes.
- Core background jobs have:
  - Structured logs
  - Error classifications
  - Alertable failure metrics
- End-to-end reliability test plan is executed with documented outcomes.

---

## Milestone 4 (Beta): Multi-workspace auth, billing hooks, usage limits

### Scope
- Introduce multi-workspace authentication/authorization.
- Add billing integration hooks (events, metering points, plan mapping).
- Enforce usage limits by plan and expose limit telemetry.

### Acceptance criteria
- Users can belong to multiple workspaces with role-based access controls.
- Workspace-scoped data isolation is enforced at API and persistence layers.
- Billing hooks emit usage events for billable actions (scan runs, tracked keywords, export operations).
- Usage limits are configurable by plan and enforced gracefully (clear UI/API errors).
- Admin/owner views include current usage vs. limit and recent billing-relevant events.

---

## Demo checklist (per milestone review)

Use this checklist before each milestone demo:

- [ ] Environment is reproducible from clean setup (seed data/scripts documented).
- [ ] Demo path is scripted from login to primary value moment (<10 minutes).
- [ ] At least one success scenario and one failure-handling scenario are shown.
- [ ] Metrics/score outputs shown in UI match underlying API payloads.
- [ ] Key logs/telemetry are visible for troubleshooting narrative.
- [ ] Known limitations and out-of-scope items are explicitly listed.
- [ ] Stakeholder feedback notes are captured live and assigned follow-ups.
- [ ] Go/no-go recommendation is recorded with open risks and mitigation plan.
