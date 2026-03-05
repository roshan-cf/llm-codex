"""URL analysis utilities for validating, fetching, and extracting prompt-grounding signals."""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Callable, Dict, List, Optional
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen
import json
import re


DEFAULT_USER_AGENT = "ai-visibility-bot/1.0 (+https://example.local/bot)"


@dataclass(slots=True)
class URLAnalysisContext:
    source_url: str
    canonical_url: str
    hostname: str
    title: str
    meta_description: str
    headings: List[str]
    visible_text_blocks: List[str]
    canonical_link: str
    schema_hints: List[str]

    def to_prompt_context(self) -> Dict[str, str]:
        return {
            "source_url": self.source_url,
            "canonical_url": self.canonical_url,
            "hostname": self.hostname,
            "page_title": self.title,
            "meta_description": self.meta_description,
            "page_headings": " | ".join(self.headings[:6]),
            "page_text_excerpt": " ".join(self.visible_text_blocks[:4]),
            "canonical_link": self.canonical_link,
            "schema_hints": ", ".join(self.schema_hints[:8]),
        }


@dataclass(slots=True)
class _NormalizedURL:
    original: str
    normalized: str
    hostname: str


class _SignalParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.meta_description = ""
        self.headings: List[str] = []
        self.visible_text_blocks: List[str] = []
        self.canonical_link = ""
        self.schema_hints: List[str] = []

        self._capture_title = False
        self._capture_heading = False
        self._skip_text_depth = 0
        self._heading_buffer: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        t = tag.lower()

        if t in {"script", "style", "noscript"}:
            self._skip_text_depth += 1
            if t == "script" and attr_map.get("type", "").lower() == "application/ld+json":
                self._skip_text_depth -= 1
                self._capture_schema_from_json_ld(attr_map)
            return

        if t == "title":
            self._capture_title = True
        if t in {"h1", "h2", "h3"}:
            self._capture_heading = True
            self._heading_buffer = []

        if t == "meta" and attr_map.get("name", "").lower() == "description":
            if not self.meta_description:
                self.meta_description = _clean_text(attr_map.get("content", ""))

        if t == "link" and "canonical" in attr_map.get("rel", "").lower():
            if not self.canonical_link:
                self.canonical_link = _clean_text(attr_map.get("href", ""))

        if "schema.org" in attr_map.get("itemtype", "").lower():
            schema_type = attr_map["itemtype"].split("/")[-1]
            if schema_type and schema_type not in self.schema_hints:
                self.schema_hints.append(schema_type)

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in {"script", "style", "noscript"} and self._skip_text_depth > 0:
            self._skip_text_depth -= 1
            return

        if t == "title":
            self._capture_title = False
        if t in {"h1", "h2", "h3"} and self._capture_heading:
            heading = _clean_text(" ".join(self._heading_buffer))
            if heading:
                self.headings.append(heading)
            self._capture_heading = False
            self._heading_buffer = []

    def handle_data(self, data: str) -> None:
        if self._skip_text_depth > 0:
            return
        cleaned = _clean_text(data)
        if not cleaned:
            return

        if self._capture_title and not self.title:
            self.title = cleaned

        if self._capture_heading:
            self._heading_buffer.append(cleaned)

        if len(cleaned) >= 35 and len(self.visible_text_blocks) < 12:
            self.visible_text_blocks.append(cleaned)

    def _capture_schema_from_json_ld(self, attrs: Dict[str, str]) -> None:
        _ = attrs

    def capture_json_ld(self, html: str) -> None:
        scripts = re.findall(
            r"<script[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        for blob in scripts:
            try:
                parsed = json.loads(blob.strip())
            except json.JSONDecodeError:
                continue
            self._ingest_schema_object(parsed)

    def _ingest_schema_object(self, obj: object) -> None:
        if isinstance(obj, dict):
            schema_type = obj.get("@type")
            if isinstance(schema_type, str) and schema_type not in self.schema_hints:
                self.schema_hints.append(schema_type)
            for value in obj.values():
                self._ingest_schema_object(value)
        elif isinstance(obj, list):
            for item in obj:
                self._ingest_schema_object(item)


class URLAnalyzer:
    def __init__(
        self,
        fetcher: Optional[Callable[[str, float, str], str]] = None,
        timeout_seconds: float = 5.0,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self.fetcher = fetcher or self._fetch_html
        self.timeout_seconds = timeout_seconds
        self.user_agent = user_agent

    def analyze(self, raw_url: str) -> URLAnalysisContext:
        normalized = self._normalize_url(raw_url)
        html = self.fetcher(normalized.normalized, self.timeout_seconds, self.user_agent)
        parser = _SignalParser()
        parser.feed(html)
        parser.capture_json_ld(html)

        canonical_link = parser.canonical_link
        if canonical_link:
            canonical_link = self._normalize_canonical(canonical_link, normalized.normalized)

        return URLAnalysisContext(
            source_url=normalized.original,
            canonical_url=canonical_link or normalized.normalized,
            hostname=normalized.hostname,
            title=parser.title,
            meta_description=parser.meta_description,
            headings=parser.headings,
            visible_text_blocks=parser.visible_text_blocks,
            canonical_link=canonical_link,
            schema_hints=parser.schema_hints,
        )

    def _normalize_url(self, raw_url: str) -> _NormalizedURL:
        candidate = raw_url.strip()
        if not candidate:
            raise ValueError("url is required")

        parsed = urlparse(candidate)
        if not parsed.scheme:
            parsed = urlparse(f"https://{candidate}")

        if parsed.scheme.lower() not in {"http", "https"}:
            raise ValueError("url scheme must be http or https")
        if not parsed.hostname:
            raise ValueError("url must include a valid hostname")

        path = parsed.path or "/"
        normalized = urlunparse(
            (
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                path,
                "",
                parsed.query,
                "",
            )
        )
        return _NormalizedURL(original=candidate, normalized=normalized, hostname=parsed.hostname.lower())

    def _normalize_canonical(self, canonical_link: str, base_url: str) -> str:
        absolute = urljoin(base_url, canonical_link)
        return self._normalize_url(absolute).normalized

    def _fetch_html(self, url: str, timeout_seconds: float, user_agent: str) -> str:
        request = Request(url, headers={"User-Agent": user_agent})
        with urlopen(request, timeout=timeout_seconds) as response:
            charset = response.headers.get_content_charset("utf-8")
            return response.read().decode(charset, errors="replace")


def _clean_text(raw: str) -> str:
    return re.sub(r"\s+", " ", raw).strip()
