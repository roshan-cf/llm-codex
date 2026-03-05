"""Quick-start first run orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List

from backend.onboarding import OnboardingState
from backend.prompt_library import PromptLibrary, PromptTemplate


@dataclass(slots=True)
class PromptExecution:
    template_key: str
    provider_name: str
    response_preview: str


@dataclass(slots=True)
class FirstRunResult:
    prompt_pack_name: str
    executions: List[PromptExecution]


class FirstRunStarter:
    """Runs a minimal prompt pack after onboarding completion."""

    def __init__(self, prompt_library: PromptLibrary | None = None) -> None:
        self.prompt_library = prompt_library or PromptLibrary()

    def run_minimal_prompt_pack(
        self,
        onboarding: OnboardingState,
        execute_prompt: Callable[[str, Dict[str, str]], str],
    ) -> FirstRunResult:
        if not onboarding.is_complete():
            raise ValueError("onboarding must be complete before first run")

        templates = self._minimal_pack()
        executions: List[PromptExecution] = []
        default_provider = next(iter(onboarding.provider_connections.keys()))
        context = {
            "primary_domain": onboarding.primary_domain,
            "industry_template": onboarding.industry_template,
            "competitors": ",".join(onboarding.competitors),
        }

        for template in templates:
            rendered_prompt = template.prompt.format(**context)
            raw = execute_prompt(rendered_prompt, {"provider": default_provider})
            executions.append(
                PromptExecution(
                    template_key=template.longitudinal_key,
                    provider_name=default_provider,
                    response_preview=raw[:140],
                )
            )

        return FirstRunResult(prompt_pack_name="first_run_minimal", executions=executions)

    def _minimal_pack(self) -> List[PromptTemplate]:
        templates = self.prompt_library.load()
        ordered_use_cases = ["informational", "commercial", "transactional"]
        selected: List[PromptTemplate] = []
        for use_case in ordered_use_cases:
            found = [template for template in templates if template.use_case == use_case]
            if found:
                selected.append(found[0])
        return selected
