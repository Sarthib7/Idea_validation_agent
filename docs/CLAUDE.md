# CLAUDE.md — VC Validation Agent

## What This Project Is

A production-grade AI agent that validates startup ideas like a VC partner. Built with FastAPI + CrewAI, wrapped in Masumi MIP-003 API standard, deployed to Sokosumi marketplace.

**Read `PRD_VC_VALIDATION_AGENT.md` first — it contains the complete architecture, schemas, and specifications.**

---

## Critical Rules

1. **MIP-003 compliance is non-negotiable.** The agent MUST implement all 5 endpoints: `/start_job`, `/status`, `/availability`, `/input_schema`, `/provide_input`. The input/output formats MUST match the MIP-003 spec exactly. See Section 2 of the PRD.

2. **The input schema in the PRD (Section 4.1) is the exact schema.** Do not simplify or modify the field IDs, types, or validation rules. The MIP-003 `input_data` format uses `{"key": "field_id", "value": "user_input"}` pairs.

3. **Masumi is payment infrastructure, NOT an agent framework.** Use `masumi-crewai` package for payment SDK only. Agent logic is pure CrewAI + FastAPI.

4. **Scope: IDEA VALIDATION ONLY.** No product testing, no deployment testing, no agent-to-agent hiring. The agent receives input, does research, and returns a validation report.

5. **This is production code.** Use proper error handling, structured logging, Pydantic models for all data boundaries, async where appropriate, and comprehensive tests.

---

## Project Structure

```
vc-validation-agent/
├── CLAUDE.md                          # This file
├── PRD_VC_VALIDATION_AGENT.md         # Full PRD — read this
├── .env.example
├── .env                               # Gitignored
├── .gitignore
├── README.md
├── requirements.txt
├── runtime.txt                        # python-3.13
│
├── main.py                            # FastAPI + MIP-003 endpoints
├── crew_definition.py                 # CrewAI crew (3 agents, 3 tasks)
│
├── config/
│   ├── __init__.py
│   ├── settings.py                    # Pydantic BaseSettings from .env
│   ├── agents.yaml                    # CrewAI agent configs
│   └── tasks.yaml                     # CrewAI task configs
│
├── schemas/
│   ├── __init__.py
│   ├── input_schema.py                # MIP-003 input schema definition
│   ├── output_schema.py               # ValidationReport Pydantic model
│   └── job.py                         # Job status tracking model
│
├── tools/
│   ├── __init__.py
│   ├── google_trends.py               # pytrends / SerpApi
│   ├── reddit_analyzer.py             # PRAW + VADER sentiment
│   ├── web_searcher.py                # SerperDev / SerpApi
│   ├── website_scraper.py             # httpx + BS4 / playwright
│   └── file_analyzer.py               # pymupdf4llm + python-pptx
│
├── analysis/
│   ├── __init__.py
│   ├── market_sizing.py               # TAM/SAM/SOM
│   ├── frameworks.py                  # Sequoia, YC, moat
│   └── scoring.py                     # Score matrix computation
│
├── prompts/
│   ├── market_researcher.md
│   ├── vc_analyst.md
│   ├── report_writer_brutal.md
│   ├── report_writer_constructive.md
│   └── report_writer_roast.md
│
├── tests/
│   ├── test_api.py
│   ├── test_tools.py
│   ├── test_analysis.py
│   └── test_e2e.py
│
├── logging_config.py
└── scripts/
    ├── register_agent.sh
    └── test_local.sh
```

---

## Environment Variables

Create `.env` from `.env.example`. Every key is documented:

```env
# Masumi Payment (REQUIRED for marketplace)
PAYMENT_SERVICE_URL=http://localhost:3001/api/v1
PAYMENT_API_KEY=
AGENT_IDENTIFIER=
SELLER_VKEY=
PAYMENT_AMOUNT=5000000
PAYMENT_UNIT=lovelace
NETWORK=Preprod

# LLM (REQUIRED — Claude is primary)
ANTHROPIC_API_KEY=

# Reddit (REQUIRED for Reddit research)
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=vc-validation-agent/1.0

# Web Search (REQUIRED — pick one)
SERPER_API_KEY=
# OR
SERPAPI_API_KEY=

# Blockchain (optional for Preprod setup)
BLOCKFROST_API_KEY_PREPROD=
```

---

## How to Build This

### Step 1: Scaffold & Dependencies

Clone the masumi quickstart template as reference:
```bash
git clone https://github.com/masumi-network/crewai-masumi-quickstart-template.git reference/
```

Then create our project from scratch using the structure above. Install:
```bash
pip install fastapi uvicorn python-dotenv masumi-crewai crewai crewai-tools \
  anthropic pytrends praw serpapi httpx beautifulsoup4 pymupdf4llm python-pptx \
  vaderSentiment pydantic aiohttp playwright
playwright install chromium
```

### Step 2: Implement MIP-003 Endpoints (main.py)

The server must handle this exact flow:

```
POST /start_job
  Body: {
    "input_data": [
      {"key": "idea_description", "value": "..."},
      {"key": "founder_stage", "value": "Just an idea — haven't started building"},
      {"key": "industry", "value": "AI / Machine Learning"},
      {"key": "feedback_tone", "value": "Brutally Honest — no sugarcoating, tell me the hard truth"},
      {"key": "goal", "value": "Validate before building"},
      ...optional fields...
    ],
    "identifier_from_purchaser": "hex_string"
  }
  
  Returns: {
    "id": "job-uuid",
    "blockchainIdentifier": "...",
    "payByTime": unix_timestamp,
    "submitResultTime": unix_timestamp,
    "unlockTime": unix_timestamp,
    "externalDisputeUnlockTime": unix_timestamp,
    "agentIdentifier": "...",
    "sellerVKey": "...",
    "identifierFromPurchaser": "...",
    "input_hash": "sha256_hash",
    "amounts": [{"amount": "5000000", "unit": "lovelace"}]
  }
```

```
GET /status?job_id=xxx
  Returns: {
    "job_id": "...",
    "status": "completed",  // or awaiting_payment, running, failed
    "result": { ... full validation report ... }
  }
```

```
GET /input_schema
  Returns: the exact schema from PRD Section 4.1
```

```
GET /availability
  Returns: { "status": "available" }
```

Use the `masumi-crewai` Payment class for payment request creation:
```python
from masumi_crewai.payment import Payment, Amount
from masumi_crewai.config import Config

config = Config(
    payment_service_url=settings.PAYMENT_SERVICE_URL,
    payment_api_key=settings.PAYMENT_API_KEY
)

payment = Payment(
    agent_identifier=settings.AGENT_IDENTIFIER,
    amounts=[Amount(amount=int(settings.PAYMENT_AMOUNT), unit=settings.PAYMENT_UNIT)],
    config=config,
    network=settings.NETWORK,
    identifier_from_purchaser=request.identifier_from_purchaser
)

response = await payment.create_payment_request()
```

### Step 3: Build Tools

Each tool should be a CrewAI-compatible tool class using `@tool` decorator or extending `BaseTool`. They must be async-capable for parallel execution.

**Google Trends Tool:** Query `interest_over_time` and `related_queries` for keywords extracted from the idea description. Return trend data with direction indicator (GROWING/STABLE/DECLINING).

**Reddit Tool:** Search top subreddits for the problem space. Use PRAW's `subreddit.search()` across `startups+SaaS+Entrepreneur+smallbusiness+indiehackers`. Run VADER sentiment on top 20-50 relevant posts. Return sentiment distribution + top pain points.

**Web Search Tool:** Use SerperDev to search for competitors, market data, and industry news. Structure results into categories.

**Website Scraper Tool:** If `website_url` is provided, fetch the page, extract key content (title, headings, meta, body text). Use `httpx` first, fall back to `playwright` for JS-heavy sites.

**File Analyzer Tool:** If `pitch_deck_file` is provided, download the file. If PDF, use `pymupdf4llm` to extract Markdown. If PPTX, use `python-pptx` to extract slide text. Return structured content.

### Step 4: Build Analysis Module

**market_sizing.py:** Given research data, estimate TAM/SAM/SOM. TAM = total market. SAM = geographic + segment constraints. SOM = realistic 3-5yr capture (typically 2-5% of SAM for early-stage SaaS).

**frameworks.py:** Implement Sequoia 10-point evaluation as a structured prompt template. Each point maps to a section of the final report. Also implement YC 5-question filter and moat analysis (network effects, switching costs, proprietary data, regulatory barriers).

**scoring.py:** Compute the 10-dimension scoring matrix. Each dimension 1-10. Overall viability = weighted average. Verdict thresholds: 80+ = STRONG OPPORTUNITY, 65-79 = PROMISING, 50-64 = NEEDS WORK, 35-49 = HIGH RISK, <35 = DO NOT PURSUE.

### Step 5: Build CrewAI Crew

Define 3 agents (Market Researcher, VC Analyst, Report Writer) with 3 sequential tasks. The Market Researcher uses all tools, the VC Analyst receives research as context, the Report Writer receives both and applies the selected tone.

Use `crew_definition.py` with the `@CrewBase` pattern. See PRD Section 5.3 for exact agent/task definitions.

The `feedback_tone` input controls which system prompt the Report Writer gets. Load the appropriate prompt from `prompts/report_writer_{tone}.md`.

### Step 6: Wire Everything Together

`main.py` → receives request → validates input → creates payment → starts background task → background task monitors payment → once paid, kicks off `VCValidationCrew` → crew runs sequentially → results stored → `/status` returns results.

Use `asyncio.create_task()` for background processing. Use a thread pool executor for the CrewAI crew (it's synchronous internally).

---

## Key Technical Decisions

- **LLM:** Use Claude (Anthropic API) as primary. Set via CrewAI's `llm` parameter on each agent.
- **Job Storage:** Use in-memory dict for development. Add PostgreSQL for production.
- **Parallel Research:** The Market Researcher agent's tools should make parallel API calls where possible using `asyncio.gather()`.
- **Error Handling:** If any tool fails (rate limit, API down), gracefully degrade — include what you got, note what failed.
- **Hashing:** Use `masumi-crewai` utility functions for input/output hashing per MIP-004.
- **Timeout:** Set a reasonable timeout (10 minutes max) for the entire crew execution.

---

## Testing Locally (Without Payments)

For development, add a bypass mode that skips payment verification:

```bash
# Run in development mode (no payment required)
DEV_MODE=true python main.py api

# Test endpoints
curl http://localhost:8000/availability
curl http://localhost:8000/input_schema

curl -X POST http://localhost:8000/start_job \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": [
      {"key": "idea_description", "value": "An AI agent marketplace where agents can hire other agents to complete complex tasks, with blockchain-based payments and verifiable work proofs"},
      {"key": "founder_stage", "value": "Early stage — have an MVP or prototype"},
      {"key": "industry", "value": "AI / Machine Learning"},
      {"key": "business_model", "value": "Marketplace / Commission"},
      {"key": "team_size", "value": "2-3 co-founders"},
      {"key": "target_audience", "value": "AI developers and businesses that want to automate complex workflows"},
      {"key": "goal", "value": "Validate before building"},
      {"key": "feedback_tone", "value": "Brutally Honest — no sugarcoating, tell me the hard truth"}
    ],
    "identifier_from_purchaser": "74657374313233"
  }'
```

---

## Quality Standards

- All public functions have docstrings
- All data boundaries use Pydantic models
- All external API calls have retry logic and timeouts
- All tools have individual unit tests
- Full end-to-end test that runs the crew with sample input
- Structured logging throughout (use `logging_config.py`)
- No hardcoded secrets — everything from `.env`
- Type hints on all function signatures
