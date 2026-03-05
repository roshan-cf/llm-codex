from backend.onboarding import OnboardingFlow, ProviderConnection
from backend.prompt_library import PromptLibrary
from backend.quickstart import FirstRunStarter


def test_onboarding_flow_completion_and_next_steps():
    flow = OnboardingFlow()

    flow.add_primary_domain("Example.com")
    flow.add_competitors(["comp-a.com", "comp-b.com"])
    flow.select_industry_template("SaaS")
    flow.confirm_provider_connections(
        [ProviderConnection(provider_name="chatgpt", connected=True)]
    )

    assert flow.state.is_complete()
    assert flow.next_steps() == []


def test_prompt_library_loads_grouping_tag_filtering_and_versions():
    library = PromptLibrary()

    grouped = library.grouped_by_use_case()

    assert {"informational", "commercial", "transactional", "brand_comparison"}.issubset(
        grouped.keys()
    )

    longitudinal_templates = library.filter_by_tags(["longitudinal"])
    assert len(longitudinal_templates) >= 2
    assert all(template.longitudinal_key.endswith(f"v{template.version}") for template in longitudinal_templates)


def test_first_run_minimal_prompt_pack_executes():
    flow = OnboardingFlow()
    flow.add_primary_domain("example.com")
    flow.add_competitors(["comp-a.com", "comp-b.com"])
    flow.select_industry_template("fintech")
    flow.confirm_provider_connections(
        [ProviderConnection(provider_name="chatgpt", connected=True)]
    )

    captured_prompts = []

    def fake_execute(prompt: str, context: dict[str, str]) -> str:
        captured_prompts.append((prompt, context))
        return "ok-response"

    result = FirstRunStarter().run_minimal_prompt_pack(flow.state, fake_execute)

    assert result.prompt_pack_name == "first_run_minimal"
    assert len(result.executions) == 3
    assert all(execution.provider_name == "chatgpt" for execution in result.executions)
    assert len(captured_prompts) == 3
