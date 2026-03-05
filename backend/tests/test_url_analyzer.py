from backend.content_ingest.url_analyzer import URLAnalysisContext, URLAnalyzer
from backend.onboarding import OnboardingFlow, ProviderConnection
from backend.quickstart import FirstRunStarter


def test_url_analyzer_normalizes_extracts_signals():
    html = """
    <html>
      <head>
        <title>Example Product Platform</title>
        <meta name="description" content="A concise summary for search and AI systems." />
        <link rel="canonical" href="/canonical-page" />
        <script type="application/ld+json">{"@context":"https://schema.org","@type":"Product"}</script>
      </head>
      <body>
        <h1>Grow revenue faster</h1>
        <h2>Built for lean marketing teams</h2>
        <p>This platform helps marketers identify audience intent and expand pipeline across key channels.</p>
        <div itemscope itemtype="https://schema.org/SoftwareApplication"></div>
      </body>
    </html>
    """

    analyzer = URLAnalyzer(fetcher=lambda url, timeout, ua: html)

    result = analyzer.analyze("Example.com/pricing#ignored")

    assert result.hostname == "example.com"
    assert result.canonical_url == "https://example.com/canonical-page"
    assert result.title == "Example Product Platform"
    assert result.meta_description == "A concise summary for search and AI systems."
    assert "Grow revenue faster" in result.headings
    assert "SoftwareApplication" in result.schema_hints
    assert "Product" in result.schema_hints


def test_first_run_starter_injects_url_analysis_context():
    flow = OnboardingFlow()
    flow.add_primary_domain("example.com")
    flow.add_competitors(["comp-a.com", "comp-b.com"])
    flow.select_industry_template("fintech")
    flow.confirm_provider_connections(
        [ProviderConnection(provider_name="chatgpt", connected=True)]
    )

    fake_context = URLAnalysisContext(
        source_url="example.com",
        canonical_url="https://example.com/",
        hostname="example.com",
        title="Example Home",
        meta_description="Best fintech software for growth.",
        headings=["Make smarter moves"],
        visible_text_blocks=["Actionable intelligence for every campaign and channel."],
        canonical_link="https://example.com/",
        schema_hints=["Organization"],
    )

    class FakeAnalyzer:
        def analyze(self, raw_url: str) -> URLAnalysisContext:
            assert raw_url == "example.com"
            return fake_context

    captured_prompts = []

    def fake_execute(prompt: str, context: dict[str, str]) -> str:
        captured_prompts.append(prompt)
        return "ok-response"

    starter = FirstRunStarter(url_analyzer=FakeAnalyzer())
    result = starter.run_minimal_prompt_pack(flow.state, fake_execute)

    assert result.prompt_pack_name == "first_run_minimal"
    assert len(captured_prompts) == 3
    assert all("Example Home" in prompt for prompt in captured_prompts)
