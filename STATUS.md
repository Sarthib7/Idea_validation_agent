# VC Validation Agent Status

Last updated: 2026-03-30

## Overall Progress

**Current weighted completion: 87%**

Formula used:

`overall_progress = sum(epic_weight * epic_completion)`

| Epic | Weight | Completion | Weighted Score | Status |
| --- | ---: | ---: | ---: | --- |
| Runtime and Python compatibility | 20% | 100% | 20.0% | Done |
| Masumi and Sokosumi request/payment compatibility | 20% | 100% | 20.0% | Done |
| VC memo formatting and output quality | 20% | 95% | 19.0% | Mostly done |
| Expanded research evidence layer | 25% | 75% | 18.8% | In progress |
| Premium diligence provider scaffolding | 5% | 20% | 1.0% | Started |
| Verification and observability | 10% | 80% | 8.0% | In progress |
| **Total** | **100%** |  | **86.8%** | **87% overall** |

## Current State

### What is working

- [x] Server runs on Python 3.13 and blocks unsupported Python 3.14+
- [x] Legacy `/start_job` payloads are normalized for Sokosumi compatibility
- [x] Missing purchaser identifiers are auto-generated safely
- [x] Free-agent registry path bypasses paid flow correctly
- [x] CrewAI now uses a supported `LLM(...)` configuration
- [x] Anthropic model fallback logic is in place
- [x] Final result is returned as a readable Markdown memo instead of raw JSON
- [x] Report includes methodology and source/reference sections
- [x] Research toolset now includes NewsAPI, GitHub, YouTube, and Similarweb hooks
- [x] Optional-tool failures degrade gracefully when keys are missing

### What is partially done

- [~] Expanded market diligence is wired, but still depends on real API keys for live coverage
- [~] Similarweb integration is implemented defensively, but not yet validated against a real account/key
- [~] GitHub tool is live, but rate-limit behavior with and without `GITHUB_TOKEN` should be observed in real runs
- [~] Report quality is strong, but the best source register quality still depends on how well the research agent preserves tool output

### What is not done yet

- [ ] Live Crunchbase integration
- [ ] Live Google Ads keyword demand sizing integration
- [ ] Automated end-to-end test covering a full research run with real external sources
- [ ] Dedicated regression tests for the new tools

## Delivered This Session

### Stability and compatibility

- Switched the project to Python 3.13 runtime expectations
- Added runtime guards to avoid CrewAI/Pydantic failures on Python 3.14+
- Fixed Masumi request compatibility issues with older Sokosumi payload shapes
- Restored the correct free-agent path by pointing at the local `pip-masumi` checkout

### Analysis and output quality

- Reworked the final response into a proper VC-style Markdown report
- Added an engagement snapshot, methodology section, and sources/references section
- Strengthened prompts so the report reads like a memo, not a raw tool dump

### Expanded research layer

- Added live tools for:
  - NewsAPI
  - GitHub repository ecosystem research
  - YouTube creator discourse
  - Similarweb traffic/rank benchmarking
- Added env/config placeholders for:
  - Crunchbase
  - Google Ads

## Live Capability Matrix

| Capability | Status | Notes |
| --- | --- | --- |
| Google Trends | Live | Existing signal source |
| Reddit sentiment | Live | Requires Reddit credentials for best results |
| Generic web search | Live | Uses Serper or SerpApi |
| Website scraping | Live | Works on accessible URLs |
| Pitch deck parsing | Live | PDF/PPTX support |
| News coverage | Live when keyed | Requires `NEWSAPI_API_KEY` |
| GitHub ecosystem signal | Live | Works without token, better with `GITHUB_TOKEN` |
| YouTube discourse | Live when keyed | Requires `YOUTUBE_API_KEY` |
| Similarweb benchmark | Live when keyed | Requires `SIMILARWEB_API_KEY` |
| Crunchbase comps/funding | Placeholder only | Env key scaffolded, not wired |
| Google Ads demand sizing | Placeholder only | Env scaffolded, not wired |

## Required Keys To Unlock More Coverage

High priority:

- `NEWSAPI_API_KEY`
- `GITHUB_TOKEN`
- `YOUTUBE_API_KEY`
- `SIMILARWEB_API_KEY`

Prepared but not yet used:

- `CRUNCHBASE_API_KEY`
- `GOOGLE_ADS_DEVELOPER_TOKEN`
- `GOOGLE_ADS_CLIENT_ID`
- `GOOGLE_ADS_CLIENT_SECRET`
- `GOOGLE_ADS_REFRESH_TOKEN`
- `GOOGLE_ADS_LOGIN_CUSTOMER_ID`

## Verification Snapshot

Verified:

- `python3 -m py_compile` passed on modified Python files
- `.venv313` import smoke test passed for `tools`, `crew_definition`, and `agent`
- New optional tools return structured missing-key responses instead of crashing

Not yet verified:

- End-to-end run with all new external API keys configured
- Quality of real Similarweb payload parsing against a live account
- Full memo quality with all new source types present in one run

## Next Recommended Steps

1. Add `NEWSAPI_API_KEY`, `GITHUB_TOKEN`, `YOUTUBE_API_KEY`, and `SIMILARWEB_API_KEY` to `.env`.
2. Run one full validation job and inspect whether the final memo cites those new sources clearly.
3. If source preservation is still weak, add a precomputed evidence pack before Crew execution.
4. After that, decide whether to wire `Crunchbase` or `Google Ads` next.

## Update Ritual

After each meaningful session:

1. Update the `Last updated` date.
2. Adjust the completion percentages in the weighted table.
3. Move checklist items between `working`, `partially done`, and `not done yet`.
4. Append one short note under `Delivered This Session` if a milestone moved materially.
