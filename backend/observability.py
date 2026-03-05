"""Lightweight observability primitives for provider and scoring pipelines."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import DefaultDict, Dict


@dataclass(slots=True)
class Observability:
    run_total: int = 0
    run_success: int = 0
    run_failure: int = 0
    provider_latency_ms: DefaultDict[str, list[float]] = field(
        default_factory=lambda: defaultdict(list)
    )
    scoring_job_duration_ms: list[float] = field(default_factory=list)
    parse_failures: DefaultDict[str, int] = field(default_factory=lambda: defaultdict(int))

    def record_run(self, *, success: bool) -> None:
        self.run_total += 1
        if success:
            self.run_success += 1
        else:
            self.run_failure += 1

    def record_provider_latency(self, provider: str, latency_ms: float) -> None:
        self.provider_latency_ms[provider].append(latency_ms)

    def record_scoring_duration(self, duration_ms: float) -> None:
        self.scoring_job_duration_ms.append(duration_ms)

    def record_parse_failure(self, parse_stage: str) -> None:
        self.parse_failures[parse_stage] += 1

    def snapshot(self) -> Dict[str, object]:
        success_rate = (self.run_success / self.run_total) if self.run_total else 0.0
        failure_rate = (self.run_failure / self.run_total) if self.run_total else 0.0
        latency_summary = {
            provider: {
                "count": len(values),
                "avg_ms": round(sum(values) / len(values), 3) if values else 0.0,
                "max_ms": round(max(values), 3) if values else 0.0,
            }
            for provider, values in self.provider_latency_ms.items()
        }
        scoring_summary = {
            "count": len(self.scoring_job_duration_ms),
            "avg_ms": (
                round(sum(self.scoring_job_duration_ms) / len(self.scoring_job_duration_ms), 3)
                if self.scoring_job_duration_ms
                else 0.0
            ),
            "max_ms": round(max(self.scoring_job_duration_ms), 3)
            if self.scoring_job_duration_ms
            else 0.0,
        }
        return {
            "run_success_rate": round(success_rate, 4),
            "run_failure_rate": round(failure_rate, 4),
            "provider_latency_ms": latency_summary,
            "scoring_job_duration_ms": scoring_summary,
            "parse_failure_counts": dict(self.parse_failures),
        }
