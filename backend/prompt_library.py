"""Prompt template loading with tags/versioning support."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List


@dataclass(slots=True)
class PromptTemplate:
    template_id: str
    version: int
    use_case: str
    title: str
    prompt: str
    tags: List[str] = field(default_factory=list)

    @property
    def longitudinal_key(self) -> str:
        return f"{self.template_id}:v{self.version}"


class PromptLibrary:
    def __init__(self, template_dir: Path | str = "data/prompt_templates") -> None:
        self.template_dir = Path(template_dir)

    def load(self) -> List[PromptTemplate]:
        templates: List[PromptTemplate] = []
        for template_file in sorted(self.template_dir.glob("*.json")):
            payload = json.loads(template_file.read_text())
            templates.extend(self._from_payload(payload))
        return templates

    def grouped_by_use_case(self) -> Dict[str, List[PromptTemplate]]:
        grouped: Dict[str, List[PromptTemplate]] = {}
        for template in self.load():
            grouped.setdefault(template.use_case, []).append(template)
        return grouped

    def filter_by_tags(self, required_tags: Iterable[str]) -> List[PromptTemplate]:
        tag_set = {tag.strip().lower() for tag in required_tags if tag.strip()}
        if not tag_set:
            return self.load()

        matched: List[PromptTemplate] = []
        for template in self.load():
            candidate = {tag.lower() for tag in template.tags}
            if tag_set.issubset(candidate):
                matched.append(template)
        return matched

    def _from_payload(self, payload: Dict[str, object]) -> List[PromptTemplate]:
        use_case = str(payload["use_case"])
        templates = payload["templates"]
        if not isinstance(templates, list):
            raise ValueError("templates must be a list")

        parsed: List[PromptTemplate] = []
        for row in templates:
            if not isinstance(row, dict):
                raise ValueError("template rows must be objects")
            parsed.append(
                PromptTemplate(
                    template_id=str(row["template_id"]),
                    version=int(row.get("version", 1)),
                    use_case=use_case,
                    title=str(row["title"]),
                    prompt=str(row["prompt"]),
                    tags=[str(tag) for tag in row.get("tags", [])],
                )
            )
        return parsed
