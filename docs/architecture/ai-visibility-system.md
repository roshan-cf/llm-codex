# AI Visibility System Architecture

## Overview

The AI Visibility System is a service-oriented platform for orchestrating prompt evaluations across multiple LLM providers, persisting raw outputs, and generating normalized, comparable scoring metrics for dashboarding.

### Primary goals

- Provide a stable control plane for creating and managing projects, domains, and prompt sets.
- Execute provider runs asynchronously and reliably at scale.
- Preserve raw provider output for traceability and reproducibility.
- Compute normalized metrics that can be compared across providers and model versions.
- Serve denormalized aggregates for low-latency dashboard and reporting use cases.

## Service split

The system is split into four services with clear ownership boundaries.

### 1. `web` service (frontend + auth)

**Responsibilities**
- Hosts the UI for workspace/project configuration and run analysis.
- Manages user authentication and session lifecycle.
- Enforces workspace-level authorization in the client-facing layer.
- Reads aggregated run/scoring views for dashboards.

**Does not do**
- Provider execution.
- Scoring computation.
- Heavy write orchestration beyond user-triggered API calls.

### 2. `api` service (project/prompt/run management)

**Responsibilities**
- Source of truth for core configuration entities.
- Creates and validates run batches.
- Emits queue messages to trigger runner jobs.
- Exposes CRUD and workflow endpoints for:
  - workspace/project/domain setup
  - prompt set and prompt management
  - run creation and lifecycle tracking

**Does not do**
- Direct execution against providers.
- Final scoring normalization math.

### 3. `runner` service (provider execution jobs)

**Responsibilities**
- Consumes queued run tasks.
- Executes provider adapters (OpenAI, Anthropic, etc.) with provider-specific retry policy.
- Persists raw provider responses and metadata.
- Emits downstream events/tasks for scoring.

**Does not do**
- End-user auth.
- Dashboard aggregation.
- Cross-provider normalization logic.

### 4. `scoring` service (normalization and metric computation)

**Responsibilities**
- Consumes completed raw response tasks.
- Applies normalization and metric computation pipelines.
- Produces immutable score snapshots per run/version.
- Maintains denormalized aggregate tables/materializations for dashboard reads.

**Does not do**
- Provider API calls.
- User/session management.

## Core entities

### `Workspace`
Top-level tenant boundary for users, access policies, and all subordinate data.

**Key fields (logical)**
- `id`
- `name`
- `created_at`, `updated_at`

### `Project`
Container for a specific evaluation initiative within a workspace.

**Key fields (logical)**
- `id`
- `workspace_id`
- `name`
- `description`
- `created_at`, `updated_at`

### `Domain`
Evaluation context/category under a project (for example: support, legal, marketing).

**Key fields (logical)**
- `id`
- `project_id`
- `name`
- `taxonomy` / `metadata`

### `PromptSet`
Versionable collection of prompts used for batch runs.

**Key fields (logical)**
- `id`
- `project_id`
- `domain_id` (optional for cross-domain sets)
- `name`
- `version`
- `is_active`

### `Prompt`
Single evaluation prompt in a prompt set.

**Key fields (logical)**
- `id`
- `prompt_set_id`
- `input_template`
- `expected_output` (optional)
- `tags`
- `ordinal`

### `ProviderRun`
Execution record for a provider/model against one prompt (or one unit of work) in a run batch.

**Key fields (logical)**
- `id`
- `workspace_id`, `project_id`
- `prompt_id`
- `provider`
- `model`
- `batch_id`
- `idempotency_key`
- `status`
- `attempt_count`
- `queued_at`, `started_at`, `finished_at`
- `error_code`, `error_message`

### `ProviderResponse`
Raw provider output and request/response metadata linked to a provider run.

**Key fields (logical)**
- `id`
- `provider_run_id`
- `raw_request`
- `raw_response`
- `latency_ms`
- `token_usage`
- `http_status`
- `provider_request_id`
- `created_at`

### `Citation`
Traceable grounding/reference extracted from provider output or scoring pipeline.

**Key fields (logical)**
- `id`
- `provider_response_id`
- `source_type`
- `source_uri`
- `span_start`, `span_end`
- `confidence`

### `ScoreSnapshot`
Immutable scoring output produced by the scoring pipeline for a run and scoring version.

**Key fields (logical)**
- `id`
- `provider_run_id`
- `scoring_version`
- `normalized_scores` (json/map)
- `composite_score`
- `dimension_scores`
- `computed_at`

## Asynchronous job flow (queue-based)

1. **API creates run batch**
   - Client initiates run from `web`.
   - `api` validates workspace/project/domain/prompt set state.
   - `api` expands prompts × providers/models into `ProviderRun` records in `QUEUED` state.
   - `api` writes queue messages keyed by `provider_run_id`.

2. **Runner executes provider adapters**
   - `runner` workers consume queue messages.
   - Job acquires idempotency lock using `idempotency_key`.
   - Provider adapter executes request.
   - Run state transitions to in-progress and terminal states (see lifecycle below).

3. **Raw responses persisted**
   - On success/failure completion, `runner` persists `ProviderResponse` (including error payloads where available).
   - `runner` updates `ProviderRun` attempt metadata and terminal status.
   - `runner` emits scoring task when response is eligible for scoring.

4. **Scoring pipeline computes normalized metrics**
   - `scoring` consumes tasks and loads raw artifacts.
   - Scoring stages:
     - validation/sanitization
     - feature extraction
     - normalization across provider/model-specific scales
     - metric and composite score computation
   - `ScoreSnapshot` is stored as immutable output (versioned by scoring config).

5. **Dashboard reads denormalized aggregates**
   - `scoring` writes/refreshes aggregate read models (for example, per provider, per domain, trend windows).
   - `web` reads these denormalized views via `api` for low-latency dashboard rendering.

## Failure, retry, and idempotency policy

### Provider-specific retry policy

Each provider adapter defines retry class behavior:

- **Retryable**: transport/network timeouts, 429 rate limit, transient 5xx.
- **Conditionally retryable**: quota errors (only if policy allows delayed retry), 409 conflict equivalents.
- **Non-retryable**: auth errors, invalid request schema, unsupported model.

Recommended defaults (overridable per provider):
- Max attempts: `3` (excluding initial enqueue).
- Backoff: exponential with jitter, e.g. `base=2s`, cap `90s`.
- Dead-letter after max attempts with terminal failure status.

### Idempotency keys

`idempotency_key` is deterministic across logical duplicate submissions:

`hash(workspace_id, project_id, prompt_id, provider, model, batch_id, prompt_version, input_fingerprint)`

Rules:
- Duplicate queued jobs with same key must not trigger duplicate provider calls when a successful terminal result already exists.
- Retries for the same `ProviderRun` reuse the same key.
- Idempotency checks happen before outbound provider call.

### Run status lifecycle

`ProviderRun.status` lifecycle:

- `QUEUED` → created by `api`, waiting in queue.
- `DISPATCHED` → worker accepted message.
- `RUNNING` → provider call in-flight.
- `SUCCEEDED` → raw response persisted and valid.
- `FAILED_RETRYABLE` → attempt failed, eligible for retry.
- `FAILED_TERMINAL` → non-retryable or max retries exceeded.
- `CANCELLED` → cancelled by user/system policy.
- `SCORING_PENDING` → success acknowledged, awaiting scoring task.
- `SCORED` → scoring completed and snapshot written.

Transition constraints:
- Terminal states: `FAILED_TERMINAL`, `CANCELLED`, `SCORED`.
- `SUCCEEDED` should transition to `SCORING_PENDING` once enqueue to scoring is confirmed.
- `SCORING_PENDING` transitions to `SCORED` only after `ScoreSnapshot` write success.
- Any invalid transition must be rejected and logged for audit.

## Data and read model strategy

- **OLTP tables**: normalized entity storage (`Workspace`, `Project`, `Domain`, `PromptSet`, `Prompt`, `ProviderRun`, `ProviderResponse`, `Citation`, `ScoreSnapshot`).
- **Read models**: denormalized aggregates for dashboard usage (materialized tables/views).
- **Auditability**: keep immutable raw provider payloads and immutable score snapshots to support replay and model comparison over time.

## Operational notes

- Prefer at-least-once queue delivery with strict idempotent consumer behavior.
- Emit structured events/metrics for each status transition and retry event.
- Add provider-level SLOs (latency, error rate, retry exhaustion) and scoring lag SLO (response persisted → score available).
