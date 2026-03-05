"""Scoring engine for AI visibility and prompt performance.

This module computes explainable metric components and weighted composite scores.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
import math
import re
from typing import Any, Callable, Iterable


TokenSet = set[str]


@dataclass(slots=True)
class WorkspaceScoreConfig:
    """Workspace-level configurable weights for score composition."""

    visibility_weights: dict[str, float] = field(
        default_factory=lambda: {
            "domain_mentions": 0.4,
            "citation_count": 0.25,
            "first_mention_rank_proxy": 0.35,
        }
    )
    performance_weights: dict[str, float] = field(
        default_factory=lambda: {
            "intent_match": 0.45,
            "brand_topic_relevance": 0.3,
            "competitor_comparison": 0.25,
        }
    )


@dataclass(slots=True)
class ScoreSnapshot:
    """Persistable score snapshot with explainability payload.

    `details_json` is intended to be saved to `ScoreSnapshot.details_json` in storage.
    """

    ai_visibility_score: float
    prompt_performance_score: float
    details_json: dict[str, Any]


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9\-\.]*", text.lower())


def _safe_weighted_average(values: dict[str, float], weights: dict[str, float]) -> float:
    numerator = 0.0
    denominator = 0.0
    for key, value in values.items():
        weight = max(weights.get(key, 0.0), 0.0)
        numerator += value * weight
        denominator += weight
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, value))


def detect_domain_mentions(
    response_text: str,
    domains: Iterable[str],
    fuzzy_threshold: float = 0.88,
) -> dict[str, Any]:
    """Detect exact and fuzzy domain mentions in response text."""

    normalized_response = _normalize_text(response_text)
    response_tokens = _tokenize(normalized_response)

    exact_mentions: list[dict[str, Any]] = []
    fuzzy_mentions: list[dict[str, Any]] = []
    first_index = math.inf

    for domain in domains:
        clean_domain = _normalize_text(domain)
        if not clean_domain:
            continue

        exact_pos = normalized_response.find(clean_domain)
        if exact_pos != -1:
            exact_mentions.append({"domain": domain, "position": exact_pos})
            first_index = min(first_index, exact_pos)
            continue

        best_ratio = 0.0
        best_window_idx = -1
        domain_parts = _tokenize(clean_domain)
        window_size = max(1, len(domain_parts))
        for i in range(0, max(1, len(response_tokens) - window_size + 1)):
            window = " ".join(response_tokens[i : i + window_size])
            ratio = SequenceMatcher(None, clean_domain, window).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_window_idx = i

        if best_ratio >= fuzzy_threshold:
            fuzzy_mentions.append(
                {
                    "domain": domain,
                    "token_position": best_window_idx,
                    "similarity": round(best_ratio, 4),
                }
            )
            first_index = min(first_index, best_window_idx)

    mention_count = len(exact_mentions) + len(fuzzy_mentions)
    total_domains = max(1, len(list(domains)) if not isinstance(domains, list) else len(domains))
    mention_score = _clip01(mention_count / total_domains)

    if first_index is math.inf:
        first_mention_rank_proxy = 0.0
    else:
        # Earlier mention => higher score.
        total_len = max(1, len(normalized_response))
        char_index = int(first_index)
        first_mention_rank_proxy = _clip01(1.0 - (char_index / total_len))

    return {
        "exact_mentions": exact_mentions,
        "fuzzy_mentions": fuzzy_mentions,
        "mention_count": mention_count,
        "mention_score": mention_score,
        "first_mention_rank_proxy": first_mention_rank_proxy,
    }


def detect_citations(response_text: str) -> dict[str, Any]:
    """Detect citation-like structures and compute citation count score."""

    url_hits = re.findall(r"https?://[^\s\)\]]+", response_text)
    markdown_links = re.findall(r"\[[^\]]+\]\((https?://[^\)]+)\)", response_text)
    bracket_citations = re.findall(r"\[(\d{1,3})\]", response_text)

    citations = {
        "urls": sorted(set(url_hits)),
        "markdown_links": sorted(set(markdown_links)),
        "bracket_indices": sorted(set(bracket_citations)),
    }
    citation_count = len(citations["urls"]) + len(citations["markdown_links"]) + len(
        citations["bracket_indices"]
    )
    # Saturate score after 4 unique citations.
    citation_score = _clip01(citation_count / 4.0)

    return {
        "citations": citations,
        "citation_count": citation_count,
        "citation_score": citation_score,
    }


def compute_intent_match(
    prompt_text: str,
    response_text: str,
    expected_intent: str,
    llm_classifier: Callable[[str, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compute intent match from deterministic checks + optional LLM classifier."""

    expected = _normalize_text(expected_intent)
    prompt_tokens: TokenSet = set(_tokenize(prompt_text))
    response_tokens: TokenSet = set(_tokenize(response_text))
    expected_tokens: TokenSet = set(_tokenize(expected))

    deterministic_overlap = 0.0
    if expected_tokens:
        deterministic_overlap = len(response_tokens & expected_tokens) / len(expected_tokens)

    prompt_alignment = 0.0
    if prompt_tokens:
        prompt_alignment = len(response_tokens & prompt_tokens) / len(prompt_tokens)

    deterministic_score = _clip01((deterministic_overlap * 0.7) + (prompt_alignment * 0.3))

    llm_label = None
    llm_confidence = 0.0
    llm_score = 0.0
    if llm_classifier:
        result = llm_classifier(prompt_text, response_text) or {}
        llm_label = _normalize_text(str(result.get("label", "")))
        llm_confidence = float(result.get("confidence", 0.0) or 0.0)
        llm_score = llm_confidence if llm_label == expected else 0.0

    intent_score = _clip01((deterministic_score * 0.6) + (llm_score * 0.4))

    return {
        "expected_intent": expected_intent,
        "deterministic_overlap": round(deterministic_overlap, 4),
        "prompt_alignment": round(prompt_alignment, 4),
        "deterministic_score": round(deterministic_score, 4),
        "llm_label": llm_label,
        "llm_confidence": round(llm_confidence, 4),
        "llm_score": round(llm_score, 4),
        "intent_score": round(intent_score, 4),
    }


def compute_brand_topic_relevance(
    response_text: str,
    brand_terms: Iterable[str],
    topic_terms: Iterable[str],
) -> dict[str, Any]:
    """Compute relevance score for brand and topic coverage."""

    response_tokens: TokenSet = set(_tokenize(response_text))
    brand_tokens: TokenSet = set(_tokenize(" ".join(brand_terms)))
    topic_tokens: TokenSet = set(_tokenize(" ".join(topic_terms)))

    brand_hit_ratio = (
        len(response_tokens & brand_tokens) / len(brand_tokens) if brand_tokens else 0.0
    )
    topic_hit_ratio = (
        len(response_tokens & topic_tokens) / len(topic_tokens) if topic_tokens else 0.0
    )

    relevance_score = _clip01((brand_hit_ratio * 0.55) + (topic_hit_ratio * 0.45))

    return {
        "brand_hit_ratio": round(brand_hit_ratio, 4),
        "topic_hit_ratio": round(topic_hit_ratio, 4),
        "relevance_score": round(relevance_score, 4),
    }


def compute_competitor_comparison_score(
    response_text: str,
    brand_name: str,
    competitors: Iterable[str],
) -> dict[str, Any]:
    """Compute score based on explicit comparison between brand and competitors."""

    normalized = _normalize_text(response_text)
    brand_norm = _normalize_text(brand_name)
    competitor_norms = [_normalize_text(c) for c in competitors if _normalize_text(c)]

    brand_mentioned = brand_norm in normalized if brand_norm else False
    mentioned_competitors = [c for c in competitor_norms if c in normalized]

    comparison_markers = ["better", "vs", "compared", "than", "alternative", "unlike"]
    marker_hits = sum(1 for marker in comparison_markers if marker in normalized)

    competitor_presence = (
        len(mentioned_competitors) / len(competitor_norms) if competitor_norms else 0.0
    )
    marker_score = _clip01(marker_hits / 3.0)

    score = _clip01(
        (0.4 if brand_mentioned else 0.0)
        + (competitor_presence * 0.35)
        + (marker_score * 0.25)
    )

    return {
        "brand_mentioned": brand_mentioned,
        "mentioned_competitors": mentioned_competitors,
        "comparison_markers": marker_hits,
        "competitor_presence": round(competitor_presence, 4),
        "marker_score": round(marker_score, 4),
        "competitor_comparison_score": round(score, 4),
    }


class ScoringEngine:
    """Computes AI visibility and prompt performance scores with explainability."""

    def __init__(self, config: WorkspaceScoreConfig | None = None) -> None:
        self.config = config or WorkspaceScoreConfig()

    def score(
        self,
        *,
        prompt_text: str,
        response_text: str,
        domains: list[str],
        expected_intent: str,
        brand_name: str,
        brand_terms: list[str],
        topic_terms: list[str],
        competitors: list[str],
        prompt_version: str,
        provider_model: str,
        run_seed: int | None = None,
        llm_classifier: Callable[[str, str], dict[str, Any]] | None = None,
    ) -> ScoreSnapshot:
        domain_metrics = detect_domain_mentions(response_text, domains)
        citation_metrics = detect_citations(response_text)

        visibility_components = {
            "domain_mentions": domain_metrics["mention_score"],
            "citation_count": citation_metrics["citation_score"],
            "first_mention_rank_proxy": domain_metrics["first_mention_rank_proxy"],
        }
        ai_visibility_score = round(
            _safe_weighted_average(visibility_components, self.config.visibility_weights), 4
        )

        intent_metrics = compute_intent_match(
            prompt_text=prompt_text,
            response_text=response_text,
            expected_intent=expected_intent,
            llm_classifier=llm_classifier,
        )
        relevance_metrics = compute_brand_topic_relevance(
            response_text=response_text,
            brand_terms=brand_terms,
            topic_terms=topic_terms,
        )
        competitor_metrics = compute_competitor_comparison_score(
            response_text=response_text,
            brand_name=brand_name,
            competitors=competitors,
        )

        performance_components = {
            "intent_match": intent_metrics["intent_score"],
            "brand_topic_relevance": relevance_metrics["relevance_score"],
            "competitor_comparison": competitor_metrics["competitor_comparison_score"],
        }
        prompt_performance_score = round(
            _safe_weighted_average(
                performance_components,
                self.config.performance_weights,
            ),
            4,
        )

        details_json = {
            "metric_components": {
                "visibility": {
                    "components": visibility_components,
                    "domain_metrics": domain_metrics,
                    "citation_metrics": citation_metrics,
                    "weights": self.config.visibility_weights,
                    "formula": "sum(component_i * weight_i) / sum(weights)",
                },
                "performance": {
                    "components": performance_components,
                    "intent_metrics": intent_metrics,
                    "relevance_metrics": relevance_metrics,
                    "competitor_metrics": competitor_metrics,
                    "weights": self.config.performance_weights,
                    "formula": "sum(component_i * weight_i) / sum(weights)",
                },
            },
            "composite_scores": {
                "ai_visibility_score": ai_visibility_score,
                "prompt_performance_score": prompt_performance_score,
            },
            "reproducibility": {
                "provider_model": provider_model,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "prompt_version": prompt_version,
                "run_seed": run_seed,
            },
        }

        return ScoreSnapshot(
            ai_visibility_score=ai_visibility_score,
            prompt_performance_score=prompt_performance_score,
            details_json=details_json,
        )
