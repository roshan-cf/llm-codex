"""Audit logging for user and system actions in the scoring workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


@dataclass(slots=True)
class AuditLogger:
    events: List[Dict[str, Any]] = field(default_factory=list)

    def _append(self, event_type: str, payload: Dict[str, Any]) -> None:
        self.events.append(
            {
                "event_type": event_type,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "payload": payload,
            }
        )

    def log_prompt_edit(self, *, actor: str, prompt_id: str, changes: Dict[str, Any]) -> None:
        self._append(
            "prompt_edit",
            {"actor": actor, "prompt_id": prompt_id, "changes": changes},
        )

    def log_run_trigger(
        self,
        *,
        actor: str,
        run_id: str,
        provider: str,
        prompt_version: str,
    ) -> None:
        self._append(
            "run_trigger",
            {
                "actor": actor,
                "run_id": run_id,
                "provider": provider,
                "prompt_version": prompt_version,
            },
        )

    def log_score_recalculation(
        self,
        *,
        actor: str,
        run_id: str,
        reason: str,
    ) -> None:
        self._append(
            "score_recalculation",
            {"actor": actor, "run_id": run_id, "reason": reason},
        )
