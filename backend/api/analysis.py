"""Analysis run API module.

Provides endpoint handlers for:
- POST /api/analysis/runs
- GET /api/analysis/runs
- GET /api/analysis/runs/{id}
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

from backend.onboarding import OnboardingFlow
from backend.providers.orchestrator import ProviderOrchestrator
from backend.scoring.engine import ScoringEngine


@dataclass(slots=True)
class AnalysisRun:
    id: str
    source_url: str
    domain: str
    provider: str
    prompt: str
    visibility: float
    quality: float
    citations: list[str]
    rawOutput: str
    status: str
    createdAt: str
    updatedAt: str
    completedAt: str | None = None
    scoreDetails: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CreateAnalysisRunRequest:
    url: str
    provider: str
    prompt: str
    expected_intent: str = "recommendation"
    brand_name: str = ""
    brand_terms: list[str] = field(default_factory=list)
    topic_terms: list[str] = field(default_factory=list)
    competitors: list[str] = field(default_factory=list)
    prompt_version: str = "v1"
    context: dict[str, Any] = field(default_factory=dict)


class AnalysisAPI:
    """In-memory endpoint handlers for analysis runs."""

    def __init__(
        self,
        *,
        orchestrator: ProviderOrchestrator,
        scoring_engine: ScoringEngine | None = None,
    ) -> None:
        self.orchestrator = orchestrator
        self.scoring_engine = scoring_engine or ScoringEngine()
        self._runs: dict[str, AnalysisRun] = {}

    def post_run(self, request: CreateAnalysisRunRequest) -> dict[str, Any]:
        source_url = request.url.strip()
        if not source_url:
            raise ValueError("url is required")

        parsed = urlparse(source_url)
        hostname = parsed.netloc or parsed.path
        cleaned_domain = self._normalize_domain(hostname)

        now = _utc_now()
        run = AnalysisRun(
            id=f"run_{uuid4().hex[:12]}",
            source_url=source_url,
            domain=cleaned_domain,
            provider=request.provider,
            prompt=request.prompt,
            visibility=0.0,
            quality=0.0,
            citations=[],
            rawOutput="",
            status="running",
            createdAt=now,
            updatedAt=now,
        )
        self._runs[run.id] = run

        response = self.orchestrator.execute(
            provider=request.provider,
            prompt=request.prompt,
            context={"domain": cleaned_domain, **request.context},
        )

        snapshot = self.scoring_engine.score(
            prompt_text=request.prompt,
            response_text=response.raw_text,
            domains=[cleaned_domain],
            expected_intent=request.expected_intent,
            brand_name=request.brand_name or cleaned_domain,
            brand_terms=request.brand_terms or [cleaned_domain],
            topic_terms=request.topic_terms,
            competitors=request.competitors,
            prompt_version=request.prompt_version,
            provider_model=response.model or response.provider,
        )

        run.provider = response.provider
        run.citations = response.citations
        run.rawOutput = response.raw_text
        run.visibility = round(snapshot.ai_visibility_score * 100, 2)
        run.quality = round(snapshot.prompt_performance_score * 100, 2)
        run.status = "completed"
        run.scoreDetails = snapshot.details_json
        run.updatedAt = _utc_now()
        run.completedAt = run.updatedAt

        return asdict(run)

    def get_runs(self) -> list[dict[str, Any]]:
        runs = sorted(self._runs.values(), key=lambda run: run.createdAt, reverse=True)
        return [asdict(run) for run in runs]

    def get_run(self, run_id: str) -> dict[str, Any]:
        run = self._runs.get(run_id)
        if not run:
            raise KeyError(f"run not found: {run_id}")
        return asdict(run)

    def _normalize_domain(self, candidate: str) -> str:
        flow = OnboardingFlow()
        flow.add_primary_domain(candidate)
        return flow.state.primary_domain


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
