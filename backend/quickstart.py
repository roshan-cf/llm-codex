"""Quick-start first run orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List

from backend.content_ingest import URLAnalyzer
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

    def __init__(
        self,
        prompt_library: PromptLibrary | None = None,
        url_analyzer: URLAnalyzer | None = None,
    ) -> None:
        self.prompt_library = prompt_library or PromptLibrary()
        self.url_analyzer = url_analyzer or URLAnalyzer()

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
        context.update(self._build_url_context(onboarding.primary_domain))

        for template in templates:
            rendered_prompt = self._render_prompt(template, context)
            raw = execute_prompt(rendered_prompt, {"provider": default_provider})
            executions.append(
                PromptExecution(
                    template_key=template.longitudinal_key,
                    provider_name=default_provider,
                    response_preview=raw[:140],
                )
            )

        return FirstRunResult(prompt_pack_name="first_run_minimal", executions=executions)


    def _render_prompt(self, template: PromptTemplate, context: Dict[str, str]) -> str:
        rendered = template.prompt.format(**context)
        grounding_bits = [
            f"URL: {context.get('canonical_url', '')}",
            f"Title: {context.get('page_title', '')}",
            f"Meta description: {context.get('meta_description', '')}",
            f"Headings: {context.get('page_headings', '')}",
            f"Schema hints: {context.get('schema_hints', '')}",
            f"Visible text: {context.get('page_text_excerpt', '')}",
        ]
        grounding = "\n".join(bit for bit in grounding_bits if not bit.endswith(': '))
        if not grounding:
            return rendered
        return f"{rendered}\n\nGrounding context from the target URL:\n{grounding}"

    def _build_url_context(self, primary_domain: str) -> Dict[str, str]:
        try:
            analysis = self.url_analyzer.analyze(primary_domain)
            return analysis.to_prompt_context()
        except Exception:
            return {
                "source_url": "",
                "canonical_url": "",
                "hostname": primary_domain,
                "page_title": "",
                "meta_description": "",
                "page_headings": "",
                "page_text_excerpt": "",
                "canonical_link": "",
                "schema_hints": "",
            }

    def _minimal_pack(self) -> List[PromptTemplate]:
        templates = self.prompt_library.load()
        ordered_use_cases = ["informational", "commercial", "transactional"]
        selected: List[PromptTemplate] = []
        for use_case in ordered_use_cases:
            found = [template for template in templates if template.use_case == use_case]
            if found:
                selected.append(found[0])
        return selected
