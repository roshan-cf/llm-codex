"""Onboarding primitives for first-run setup."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class OnboardingStep(str, Enum):
    ADD_PRIMARY_DOMAIN = "add_primary_domain"
    ADD_COMPETITORS = "add_competitors"
    SELECT_INDUSTRY_TEMPLATE = "select_industry_template"
    CONFIRM_PROVIDER_CONNECTIONS = "confirm_provider_connections"


@dataclass(slots=True)
class ProviderConnection:
    provider_name: str
    connected: bool
    details: str = ""


@dataclass(slots=True)
class OnboardingState:
    primary_domain: str = ""
    competitors: List[str] = field(default_factory=list)
    industry_template: str = ""
    provider_connections: Dict[str, ProviderConnection] = field(default_factory=dict)

    def completed_steps(self) -> List[OnboardingStep]:
        steps: List[OnboardingStep] = []
        if self.primary_domain:
            steps.append(OnboardingStep.ADD_PRIMARY_DOMAIN)
        if 2 <= len(self.competitors) <= 5:
            steps.append(OnboardingStep.ADD_COMPETITORS)
        if self.industry_template:
            steps.append(OnboardingStep.SELECT_INDUSTRY_TEMPLATE)
        if self.provider_connections and all(
            connection.connected for connection in self.provider_connections.values()
        ):
            steps.append(OnboardingStep.CONFIRM_PROVIDER_CONNECTIONS)
        return steps

    def is_complete(self) -> bool:
        return len(self.completed_steps()) == len(OnboardingStep)


class OnboardingFlow:
    """Small stateful helper used by API handlers/CLI entrypoints."""

    def __init__(self) -> None:
        self.state = OnboardingState()

    def add_primary_domain(self, domain: str) -> None:
        cleaned = domain.strip().lower()
        if not cleaned or "." not in cleaned:
            raise ValueError("primary domain must be a valid hostname")
        self.state.primary_domain = cleaned

    def add_competitors(self, competitors: List[str]) -> None:
        normalized = [entry.strip().lower() for entry in competitors if entry.strip()]
        deduped = list(dict.fromkeys(normalized))
        if not 2 <= len(deduped) <= 5:
            raise ValueError("competitors must include between 2 and 5 domains")
        self.state.competitors = deduped

    def select_industry_template(self, template_slug: str) -> None:
        cleaned = template_slug.strip().lower().replace(" ", "-")
        if not cleaned:
            raise ValueError("industry template slug is required")
        self.state.industry_template = cleaned

    def confirm_provider_connections(self, connections: List[ProviderConnection]) -> None:
        if not connections:
            raise ValueError("at least one provider connection is required")
        self.state.provider_connections = {
            connection.provider_name: connection for connection in connections
        }

    def next_steps(self) -> List[OnboardingStep]:
        completed = set(self.state.completed_steps())
        return [step for step in OnboardingStep if step not in completed]
