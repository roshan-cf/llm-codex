# MVP Product Brief: AI Visibility Platform

## 1) Product Overview
The AI Visibility MVP helps teams understand and improve how often their brand/domain appears in AI-generated answers. The product runs structured prompt sets across leading AI providers and returns normalized visibility and performance scoring.

### Problem Statement
As user discovery shifts from traditional search results to AI assistants, teams lack a practical way to measure whether their domain is present, favored, and positively represented in AI responses. Current workflows are manual, inconsistent, and hard to compare over time.

### MVP Goal
Deliver a lightweight, repeatable system that allows teams to:
- onboard one domain,
- run standardized prompts across selected providers,
- measure visibility and quality outcomes,
- benchmark against competitors in a scoring dashboard.

## 2) Target Users

### SEO Lead
Owns organic discoverability goals and needs a reliable signal for AI-era brand presence.

### Content Strategist
Optimizes topic coverage, authority signals, and messaging so AI systems cite/mention the domain.

### Growth PM
Needs channel-level performance data to prioritize experiments and investment in content/distribution.

## 3) Top 3 Jobs-to-be-Done (JTBD)
1. **Measure AI visibility:** “Help me quantify how often my domain appears across key AI providers for my strategic prompts.”
2. **Diagnose performance gaps:** “Help me identify where we are underperforming (position, tone, quality alignment) so I can prioritize improvements.”
3. **Track competitive standing:** “Help me compare our share-of-voice versus competitors to guide roadmap and go-to-market decisions.”

## 4) Locked MVP Features (v1)

### 4.1 Domain Onboarding
- Accept a **single website URL** as the tracked domain.
- Normalize domain variants (www/non-www, http/https) for reporting consistency.

### 4.2 Prompt Set Management
- Create, edit, and store reusable prompt sets.
- Group prompts by use case (brand, category, comparison, problem-solution, educational intent).
- Support versioning metadata for prompt set iterations.

### 4.3 Provider Runs
Execute prompt sets against:
- **ChatGPT**
- **Perplexity**
- **Gemini**
- **Google AI Overview proxy workflow**

Run behavior:
- Batch run prompts by provider.
- Persist raw response text and provider metadata for scoring.
- Support reruns to observe variance over time.

### 4.4 Scoring Dashboard
Unified dashboard with:
- **Visibility score** (presence and prominence of tracked domain),
- **Performance score** (quality + stance + comparative outcomes),
- Provider-level and prompt-level drill-downs,
- Trend view by run timestamp.

## 5) Measurable KPIs

### Mention Rate
- Definition: **% of prompts where tracked domain is cited or mentioned**.
- Formula: `(prompts_with_domain_mention / total_prompts_run) * 100`.

### Rank Position in Response (if detectable)
- Definition: Average detected position of tracked domain among cited/recommended options within a response.
- Notes: Capture only when explicit ordering can be inferred; otherwise mark as non-detectable.

### Sentiment/Stance Score
- Definition: Normalized score representing whether the response framing about the domain is positive, neutral, or negative.
- Example scale: `-1.0` (negative) to `+1.0` (positive).

### Response Quality Alignment Score
- Definition: Score indicating how well the response representation of the domain aligns with desired positioning criteria (accuracy, relevance, value proposition fit).
- Implementation approach: rubric-based scoring using predefined criteria per prompt category.

### Share-of-Voice vs Competitors
- Definition: Relative proportion of mentions for tracked domain versus configured competitor domains across the same prompt/provider set.
- Formula: `tracked_domain_mentions / total_mentions_of_tracked_plus_competitors`.

## 6) Explicit Limitations

### ToS and Platform Constraints
- Data collection and automation must comply with each provider’s Terms of Service and usage policies.
- Some providers may restrict automation, replay, or large-scale extraction patterns.

### Scraping Restrictions
- The MVP should avoid prohibited scraping techniques and rely on permitted interfaces/proxy workflows.
- Structured extraction may be partially constrained by dynamic UI or anti-bot controls.

### Model Variability
- Output quality and citation behavior differ significantly by provider and model version.
- Cross-provider comparisons should be interpreted directionally, not as strict equivalence.

### Non-determinism
- Repeated identical prompts can produce different outputs over time.
- KPI interpretation should emphasize trends and sample sizes rather than single-run absolutes.

## 7) Out of Scope for v1
- **Real-time monitoring** and alerting.
- **Full SERP crawling** or broad web index replication.
- **Autonomous prompt generation** (self-updating prompt discovery/creation).

## 8) Success Criteria for MVP Readiness
- Users can onboard one domain and run at least one prompt set across all four target provider workflows.
- Dashboard surfaces all five KPI families with prompt/provider drill-down.
- Users can compare at least one run against competitor share-of-voice output.
- Product documentation clearly communicates limitations and confidence caveats.
