"""Secrets loading helpers for env vars and server-side key vault lookups."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Optional, Protocol


class KeyVault(Protocol):
    """Protocol for a server-side key vault client."""

    def get_secret(self, secret_ref: str) -> Optional[str]:
        """Resolve a secret value from a vault reference."""


@dataclass(slots=True)
class EnvManager:
    """Small abstraction around environment access for deterministic config loading."""

    environ: Dict[str, str]

    @classmethod
    def from_os(cls) -> "EnvManager":
        return cls(dict(os.environ))

    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        value = self.environ.get(name)
        return value if value not in (None, "") else default


class NullKeyVault:
    """Fallback vault implementation when no vault integration is configured."""

    def get_secret(self, secret_ref: str) -> Optional[str]:
        return None
