# PRD: VC-Style Startup Idea Validation Agent

**Version:** 2.0
**Date:** March 30, 2026
**Status:** Ready for Implementation
**Platform:** Masumi Network → Sokosumi Marketplace

---

## 1. Executive Summary

Build a production-grade AI agent that acts as a **VC partner evaluating a startup idea**. The agent receives structured founder input (idea description, stage, goals, team, optional pitch deck/website), conducts autonomous research using Google Trends, Reddit, and web search, then delivers a professional **investment-grade validation report** with a Go/No-Go verdict, confidence scores, and detailed reasoning matrices.

The agent is built with **FastAPI + CrewAI**, wrapped in the **Masumi MIP-003 API standard**, and listed on the **Sokosumi marketplace** for monetization via Cardano blockchain payments.

**Scope: Idea validation and feedback ONLY. No product testing, no deployment testing, no agent hiring.**

---

## 2. How Masumi Works (Critical Context for Implementation)

Masumi is **NOT an agent framework** — it is blockchain payment infrastructure. The actual agent logic is built with CrewAI/FastAPI, then wrapped in MIP-003 compliant endpoints.

### 2.1 The Sumi Ecosystem

| Platform | Purpose |
|----------|---------|
| **Masumi** | Protocol — payments + identity on Cardano blockchain |
| **Sokosumi** | Marketplace — where users discover and hire agents |
| **Kodosumi** | Runtime — hosting/deployment for agents |

### 2.2 MIP-003 Required Endpoints

Every Masumi-compatible agent MUST implement these 5 endpoints:

```
GET  /availability      → Health check (returns "available" or "unavailable")
GET  /input_schema      → Returns expected input format (field types, validations)
POST /start_job         → Initiates a job, returns payment details
GET  /status            → Returns job status (awaiting_payment → running → completed)
POST /provide_input     → Supplies additional data for multi-step jobs (optional for us)
```

### 2.3 Payment Flow

```
User calls /start_job with input_data
  → Agent creates payment request via Masumi Payment Service
  → Returns job_id + payment details (blockchain address, amounts, deadlines)
  → User pays on Cardano blockchain (USDM stablecoin or lovelace)
  → Payment Service detects payment
  → Agent starts processing (status: "running")
  → Agent completes work (status: "completed")
  → Results delivered, funds released to seller wallet
```

### 2.4 Package: `masumi-crewai`

```bash
pip install masumi-crewai
```

Key classes:
- `Payment` — seller-side transaction management
- `Purchase` — buyer-side operations (not needed for us)
- `Config` — API keys, payment service URL
- `Amount` — payment amount + unit specification

### 2.5 Template Repository

Clone from: `https://github.com/masumi-network/crewai-masumi-quickstart-template`

File structure:
```
├── .env.example
├── crew_definition.py    ← Define agents and tasks here
├── main.py               ← FastAPI server with MIP-003 endpoints
├── logging_config.py
├── requirements.txt
└── runtime.txt
```

---

## 3. Agent Purpose & Philosophy

### 3.1 Core Question the Agent Answers

> **"Will this idea work? Why or why not?"**

The agent thinks like a **top-tier VC partner** at Sequoia, YC, or a16z. It doesn't just give opinions — it does actual research, applies proven investment frameworks, and delivers a structured verdict with full reasoning transparency.

### 3.2 What Makes This Different from Competitors

| Competitor | What they do | What they lack |
|-----------|-------------|---------------|
| AI CoFounder ($39-85/mo) | 8-phase founder coaching, 75+ sources | No VC frameworks, no scoring, no pitch deck analysis |
| DimeADozen.ai ($39/report) | 40-page SWOT reports | No real-time data, no tone options |
| ValidatorAI (free) | Conversational validation | Limited depth, basic scoring |
| IdeaProof | 120-second validation | Surface level, no research |
| **Our Agent** | **Real-time data + VC frameworks + adjustable tone + file input** | **This gap is unoccupied** |

---

## 4. Input Schema (MIP-003 Compliant)

### 4.1 Schema Definition

The `/input_schema` endpoint returns this exact structure:

```json
{
  "input_data": [
    {
      "id": "idea_description",
      "type": "string",
      "name": "Describe Your Idea",
      "data": {
        "description": "Tell us about your startup idea. What problem does it solve? Who is it for? How does it work? Be as detailed as possible."
      },
      "validations": [
        { "validation": "min", "value": "50" }
      ]
    },
    {
      "id": "founder_stage",
      "type": "option",
      "name": "What stage are you at?",
      "data": {
        "values": [
          "Just an idea — haven't started building",
          "Early stage — have an MVP or prototype",
          "Growth stage — have users/revenue",
          "Scaling — looking for investment"
        ]
      },
      "validations": [
        { "validation": "min", "value": "1" },
        { "validation": "max", "value": "1" }
      ]
    },
    {
      "id": "industry",
      "type": "option",
      "name": "Industry / Vertical",
      "data": {
        "values": [
          "SaaS / Software",
          "AI / Machine Learning",
          "Fintech / Payments",
          "Healthcare / Biotech",
          "E-commerce / Marketplace",
          "Education / EdTech",
          "Climate / Clean Energy",
          "Web3 / Blockchain",
          "Consumer / Social",
          "Hardware / IoT",
          "Other"
        ]
      },
      "validations": [
        { "validation": "min", "value": "1" },
        { "validation": "max", "value": "1" }
      ]
    },
    {
      "id": "target_audience",
      "type": "string",
      "name": "Target Audience",
      "data": {
        "description": "Who are your ideal customers? B2B or B2C? What's their demographic or firmographic profile?"
      }
    },
    {
      "id": "business_model",
      "type": "option",
      "name": "Business Model",
      "data": {
        "values": [
          "Subscription (SaaS)",
          "Marketplace / Commission",
          "Freemium",
          "One-time purchase",
          "Advertising",
          "Usage-based / Pay-per-use",
          "Enterprise licensing",
          "Not decided yet"
        ]
      },
      "validations": [
        { "validation": "min", "value": "1" },
        { "validation": "max", "value": "1" }
      ]
    },
    {
      "id": "team_size",
      "type": "option",
      "name": "Team Size",
      "data": {
        "values": [
          "Solo founder",
          "2-3 co-founders",
          "Small team (4-10)",
          "Growing team (11-50)",
          "Large team (50+)"
        ]
      },
      "validations": [
        { "validation": "min", "value": "1" },
        { "validation": "max", "value": "1" }
      ]
    },
    {
      "id": "existing_traction",
      "type": "string",
      "name": "Existing Traction (optional)",
      "data": {
        "description": "Any users, revenue, waitlist, LOIs, partnerships? Share numbers if you have them."
      }
    },
    {
      "id": "competitors",
      "type": "string",
      "name": "Known Competitors (optional)",
      "data": {
        "description": "List any competitors or similar products you know about."
      }
    },
    {
      "id": "unique_advantage",
      "type": "string",
      "name": "What's your unfair advantage? (optional)",
      "data": {
        "description": "Proprietary tech, domain expertise, network effects, unique data, patents, etc."
      }
    },
    {
      "id": "goal",
      "type": "option",
      "name": "What's your primary goal?",
      "data": {
        "values": [
          "Validate before building",
          "Prepare for fundraising",
          "Decide whether to pivot",
          "Understand the market better",
          "Get honest feedback on viability"
        ]
      },
      "validations": [
        { "validation": "min", "value": "1" },
        { "validation": "max", "value": "1" }
      ]
    },
    {
      "id": "feedback_tone",
      "type": "option",
      "name": "Feedback Style",
      "data": {
        "values": [
          "Brutally Honest — no sugarcoating, tell me the hard truth",
          "Constructive — balanced feedback with improvement suggestions",
          "Roast Me — savage, funny, but still insightful"
        ]
      },
      "validations": [
        { "validation": "min", "value": "1" },
        { "validation": "max", "value": "1" }
      ]
    },
    {
      "id": "website_url",
      "type": "string",
      "name": "Website or Landing Page URL (optional)",
      "data": {
        "description": "If you have a website, landing page, or GitHub repo, paste the URL here."
      },
      "validations": [
        { "validation": "format", "value": "url" }
      ]
    },
    {
      "id": "pitch_deck_file",
      "type": "string",
      "name": "Pitch Deck File URL (optional)",
      "data": {
        "description": "Link to your pitch deck (PDF, Google Slides link, or hosted file URL)."
      }
    }
  ]
}
```

### 4.2 Input Categories

**Required fields (must have):**
- `idea_description` — the core idea text (min 50 chars)
- `founder_stage` — dropdown selection
- `industry` — dropdown selection
- `feedback_tone` — dropdown selection
- `goal` — dropdown selection

**Structured dropdowns (easy for user):**
- `founder_stage`, `industry`, `business_model`, `team_size`, `goal`, `feedback_tone`

**Optional free text:**
- `target_audience`, `existing_traction`, `competitors`, `unique_advantage`

**Optional file/link inputs:**
- `website_url` — agent will scrape and analyze
- `pitch_deck_file` — agent will download, parse PDF/PPTX, and analyze

---

## 5. Agent Architecture

### 5.1 High-Level Flow

```
User submits via /start_job
  │
  ├── 1. INPUT PARSING
  │     Parse all fields, validate required, detect optional enrichments
  │     If website_url provided → queue web scraping
  │     If pitch_deck_file provided → queue file download + extraction
  │
  ├── 2. AUTONOMOUS RESEARCH (parallel via asyncio)
  │     ├── Google Trends Analysis (pytrends or SerpApi)
  │     │     • Interest over time for idea keywords
  │     │     • Related queries (identify "Breakout" signals)
  │     │     • Geographic interest distribution
  │     │     • Compare against competitor keywords
  │     │
  │     ├── Reddit Sentiment Analysis (PRAW or web scraping)
  │     │     • Search r/startups, r/SaaS, r/Entrepreneur, r/smallbusiness, r/indiehackers
  │     │     • Find discussions about the problem space
  │     │     • VADER sentiment analysis on relevant posts
  │     │     • Extract pain points and unmet needs
  │     │
  │     ├── Web Search (SerperDev or SerpApi)
  │     │     • Competitor landscape scan
  │     │     • Recent funding in the space
  │     │     • Market size data points
  │     │     • News/trends in the industry
  │     │
  │     ├── Website Analysis (if URL provided)
  │     │     • Scrape landing page content
  │     │     • Analyze messaging, positioning, clarity
  │     │     • Check basic tech stack signals
  │     │     • Lighthouse-style performance check (optional)
  │     │
  │     └── Pitch Deck Analysis (if file provided)
  │           • Extract text from PDF via pymupdf4llm
  │           • Analyze slide-by-slide against Sequoia framework
  │           • Identify missing sections
  │           • Evaluate quality of claims and data
  │
  ├── 3. VC FRAMEWORK ANALYSIS (LLM synthesis)
  │     ├── Sequoia 10-Point Evaluation
  │     │     Company Purpose, Problem, Solution, Why Now,
  │     │     Market Potential, Competition, Business Model,
  │     │     Team, Financials, Vision
  │     │
  │     ├── TAM/SAM/SOM Market Sizing
  │     │     • TAM: Total addressable market
  │     │     • SAM: Serviceable addressable market
  │     │     • SOM: Serviceable obtainable market (realistic 3-5yr)
  │     │
  │     ├── Unit Economics Assessment
  │     │     • Estimated CAC, LTV, LTV:CAC ratio
  │     │     • Payback period estimate
  │     │     • Margin analysis based on business model
  │     │
  │     ├── Competitive Moat Analysis
  │     │     • Network effects, switching costs, proprietary data
  │     │     • Regulatory barriers, brand, economies of scale
  │     │
  │     └── YC 5-Question Filter
  │           1. Is this idea interesting?
  │           2. Is the founder/team impressive?
  │           3. Can they explain it clearly?
  │           4. Have they made progress?
  │           5. Is it venture-scale?
  │
  ├── 4. VERDICT GENERATION
  │     ├── Overall Viability Score (0-100)
  │     ├── Verdict: STRONG OPPORTUNITY / PROMISING / NEEDS WORK / HIGH RISK / DO NOT PURSUE
  │     ├── Confidence Level: HIGH / MEDIUM / LOW
  │     ├── Go/No-Go Recommendation with reasoning
  │     │
  │     └── Scoring Matrix (each rated 1-10 with explanation):
  │           • Market Opportunity
  │           • Problem Severity
  │           • Solution Quality
  │           • Timing (Why Now)
  │           • Competitive Advantage
  │           • Business Model Viability
  │           • Team Readiness
  │           • Scalability Potential
  │           • Risk Level (inverse — lower is riskier)
  │           • Overall Investment Potential
  │
  └── 5. REPORT GENERATION (tone-adjusted)
        Apply selected feedback_tone to the entire output:
        • "Brutally Honest" — harsh, direct, identifies fatal flaws first
        • "Constructive" — balanced, includes alternative suggestions
        • "Roast Me" — savage humor but still data-backed insights
```

### 5.2 CrewAI Agent Definitions

The agent uses a **multi-agent crew** with specialized roles:

```
Agent 1: MARKET RESEARCHER
  Role: Senior Market Research Analyst
  Goal: Gather real-time market data, trends, and competitive intelligence
  Tools: Google Trends, Reddit scraper, Web search, Website scraper
  Backstory: "You're a senior analyst at a top VC firm. You dig deep into
              market data before any partner meeting. You find the real
              numbers, not the vanity metrics."

Agent 2: VC ANALYST
  Role: Principal at a Top-Tier VC Fund
  Goal: Apply formal VC evaluation frameworks to the research data
  Tools: None (pure analysis — receives research data as context)
  Backstory: "You've evaluated 10,000+ startup pitches at firms like
              Sequoia, YC, and a16z. You know exactly what separates
              billion-dollar ideas from zombie startups. You apply
              rigorous frameworks but also trust pattern recognition
              from years of experience."

Agent 3: REPORT WRITER
  Role: Investment Memo Writer
  Goal: Synthesize all analysis into a professional, tone-adjusted report
  Tools: None (pure writing)
  Backstory: "You write the investment memos that decide whether partners
              write checks. Your reports are clear, data-backed, and
              brutally honest about risks. You adjust your tone from
              boardroom-formal to roast-comedy depending on what's asked."
```

### 5.3 CrewAI Task Flow

```
Task 1: market_research_task
  Agent: Market Researcher
  Description: Research the market for the given idea using all available tools.
               Search Google Trends, Reddit, and the web. If a URL is provided,
               scrape it. If a pitch deck is provided, analyze it.
  Expected Output: Structured research findings (JSON)

Task 2: vc_analysis_task
  Agent: VC Analyst
  Context: [market_research_task]
  Description: Apply Sequoia 10-point framework, TAM/SAM/SOM, unit economics,
               moat analysis, and YC 5-question filter to the research data.
               Score each dimension 1-10. Generate verdict and confidence level.
  Expected Output: Structured analysis (JSON with scores and reasoning)

Task 3: report_generation_task
  Agent: Report Writer
  Context: [market_research_task, vc_analysis_task]
  Description: Write the final validation report using the specified feedback tone.
               Include all scores, reasoning, verdict, and actionable next steps.
  Expected Output: Complete validation report (Markdown)
```

---

## 6. Output Structure

The agent returns a structured validation report. Here's the schema:

```json
{
  "job_id": "uuid",
  "status": "completed",
  "result": {
    "verdict": "PROMISING",
    "viability_score": 72,
    "confidence": "MEDIUM",
    "go_no_go": "CONDITIONAL GO — address key risks first",

    "scoring_matrix": {
      "market_opportunity":      { "score": 8, "reason": "..." },
      "problem_severity":        { "score": 7, "reason": "..." },
      "solution_quality":        { "score": 6, "reason": "..." },
      "timing_why_now":          { "score": 9, "reason": "..." },
      "competitive_advantage":   { "score": 5, "reason": "..." },
      "business_model_viability":{ "score": 7, "reason": "..." },
      "team_readiness":          { "score": 6, "reason": "..." },
      "scalability_potential":   { "score": 8, "reason": "..." },
      "risk_assessment":         { "score": 5, "reason": "..." },
      "investment_potential":    { "score": 7, "reason": "..." }
    },

    "executive_summary": "2-3 paragraph investment thesis...",

    "market_analysis": {
      "tam_estimate": "$X billion",
      "sam_estimate": "$X billion",
      "som_estimate": "$X million",
      "trend_direction": "GROWING / STABLE / DECLINING",
      "google_trends_summary": "...",
      "reddit_sentiment_summary": "...",
      "key_competitors": ["...", "..."],
      "market_gaps_identified": ["...", "..."]
    },

    "strengths": ["...", "..."],
    "weaknesses": ["...", "..."],
    "opportunities": ["...", "..."],
    "threats": ["...", "..."],

    "critical_risks": [
      { "risk": "...", "severity": "HIGH", "mitigation": "..." }
    ],

    "actionable_next_steps": [
      { "priority": 1, "action": "...", "timeline": "..." }
    ],

    "pitch_deck_feedback": "... (only if file was provided)",
    "website_feedback": "... (only if URL was provided)",

    "full_report_markdown": "... complete formatted report with tone applied ..."
  }
}
```

---

## 7. Tech Stack & Dependencies

### 7.1 Core Dependencies

```txt
# requirements.txt

# Framework
fastapi>=0.104.0
uvicorn>=0.24.0
python-dotenv>=1.0.0

# Masumi Integration
masumi-crewai>=0.1.26

# AI Agent Framework
crewai>=0.100.0
crewai-tools>=0.17.0

# LLM
anthropic>=0.40.0          # Claude API for primary LLM
openai>=1.50.0             # Fallback / alternative

# Data Collection Tools
pytrends>=4.9.2            # Google Trends (NOTE: archived, may need SerpApi fallback)
praw>=7.7.1                # Reddit API
serpapi>=2.0.0             # Google Search + Trends fallback (paid, 100 free/mo)
httpx>=0.27.0              # Async HTTP client
beautifulsoup4>=4.12.0     # HTML parsing
playwright>=1.40.0         # JS-heavy website scraping (install browsers separately)

# File Processing
pymupdf4llm>=0.0.10        # PDF → Markdown extraction (fastest)
python-pptx>=0.6.23        # PowerPoint parsing

# Sentiment Analysis
vaderSentiment>=3.3.2       # Reddit-optimized sentiment

# Data Validation
pydantic>=2.5.0            # Structured output schemas

# Utilities
asyncio                    # Built-in async orchestration
aiohttp>=3.9.0             # Async HTTP for masumi-crewai
```

### 7.2 API Keys Required

```env
# .env file

# ===== MASUMI NETWORK (REQUIRED) =====
PAYMENT_SERVICE_URL=http://localhost:3001/api/v1
PAYMENT_API_KEY=your_masumi_payment_api_key
AGENT_IDENTIFIER=your_agent_identifier_from_registration
SELLER_VKEY=your_selling_wallet_verification_key
PAYMENT_AMOUNT=5000000          # Price in lovelace (5 ADA) or USDM
PAYMENT_UNIT=lovelace           # or specific USDM policy_id.token_name
NETWORK=Preprod                 # Start with Preprod, switch to Mainnet for production

# ===== LLM API (REQUIRED — at least one) =====
ANTHROPIC_API_KEY=sk-ant-...    # Claude API — primary LLM for all analysis
OPENAI_API_KEY=sk-...           # Optional fallback

# ===== DATA SOURCES =====
# Reddit API (REQUIRED for Reddit research)
REDDIT_CLIENT_ID=your_reddit_app_client_id
REDDIT_CLIENT_SECRET=your_reddit_app_secret
REDDIT_USER_AGENT=vc-validation-agent/1.0

# Google Search (REQUIRED for web search — pick one)
SERPER_API_KEY=your_serper_key           # SerperDev — $50/mo for 2500 searches
# OR
SERPAPI_API_KEY=your_serpapi_key          # SerpApi — 100 free/mo, then paid

# Google Trends (OPTIONAL — pytrends is free but archived, SerpApi is paid)
# If using SerpApi for trends, same key as above works

# ===== OPTIONAL =====
BLOCKFROST_API_KEY_PREPROD=your_blockfrost_key  # Cardano blockchain queries
```

### 7.3 Where to Get Each API Key

| Service | URL | Free Tier | Notes |
|---------|-----|-----------|-------|
| Masumi Payment Service | Run locally via Docker or Railway | Free on Preprod | See setup guide below |
| Anthropic Claude API | https://console.anthropic.com | $5 free credit | Primary LLM |
| Reddit API | https://www.reddit.com/prefs/apps | Free (100 req/min) | Create "script" type app |
| SerperDev | https://serper.dev | 2,500 free queries | Google Search API |
| SerpApi | https://serpapi.com | 100 free/mo | Google Search + Trends |
| Blockfrost | https://blockfrost.io | Free tier | Cardano blockchain API |

---

## 8. Project File Structure

```
vc-validation-agent/
├── CLAUDE.md                        # Instructions for Claude Code
├── .env.example                     # Template for environment variables
├── .env                             # Actual env vars (gitignored)
├── .gitignore
├── README.md
├── requirements.txt
├── runtime.txt                      # Python version (python-3.13)
├── pyproject.toml                   # Optional — for uv/pip
│
├── main.py                          # FastAPI server — MIP-003 endpoints
│                                    #   /start_job, /status, /availability,
│                                    #   /input_schema, /provide_input
│
├── crew_definition.py               # CrewAI crew — agents + tasks
│
├── config/
│   ├── __init__.py
│   ├── settings.py                  # Pydantic settings from .env
│   ├── agents.yaml                  # CrewAI agent definitions
│   └── tasks.yaml                   # CrewAI task definitions
│
├── schemas/
│   ├── __init__.py
│   ├── input_schema.py              # MIP-003 input schema definition
│   ├── output_schema.py             # Pydantic models for validation report
│   └── job.py                       # Job status model
│
├── tools/
│   ├── __init__.py
│   ├── google_trends.py             # Google Trends data collector
│   ├── reddit_analyzer.py           # Reddit search + VADER sentiment
│   ├── web_searcher.py              # Web search via SerperDev/SerpApi
│   ├── website_scraper.py           # Website URL scraper + analyzer
│   └── file_analyzer.py             # PDF/PPTX pitch deck parser
│
├── analysis/
│   ├── __init__.py
│   ├── market_sizing.py             # TAM/SAM/SOM calculation logic
│   ├── frameworks.py                # Sequoia, YC, moat analysis frameworks
│   └── scoring.py                   # Scoring matrix computation
│
├── prompts/
│   ├── market_researcher.md         # System prompt for research agent
│   ├── vc_analyst.md                # System prompt for VC analysis agent
│   ├── report_writer_brutal.md      # Brutally honest tone prompt
│   ├── report_writer_constructive.md # Constructive tone prompt
│   └── report_writer_roast.md       # Roast tone prompt
│
├── tests/
│   ├── test_api.py                  # MIP-003 endpoint tests
│   ├── test_tools.py                # Tool unit tests
│   ├── test_analysis.py             # Analysis framework tests
│   └── test_e2e.py                  # End-to-end validation flow
│
├── logging_config.py                # Structured logging setup
│
└── scripts/
    ├── register_agent.sh            # Script to register on Masumi
    └── test_local.sh                # Local testing script
```

---

## 9. Implementation Details

### 9.1 main.py — MIP-003 Server

This is the FastAPI server. It handles all MIP-003 endpoints and orchestrates the crew.

Key responsibilities:
- `/input_schema` → returns the schema from Section 4.1
- `/start_job` → validates input against schema, creates payment request via `masumi-crewai`, starts background job
- `/status` → returns job status and results when complete
- `/availability` → returns `"available"`
- Jobs stored in a dict for dev, **PostgreSQL for production**

The `/start_job` endpoint:
1. Receives `input_data` (array of key-value pairs) + `identifier_from_purchaser`
2. Validates input against schema
3. Creates payment request via Masumi Payment SDK
4. Returns job_id, payment details, deadlines
5. Starts a background async task that monitors payment → runs crew → stores result

### 9.2 crew_definition.py — Agent Logic

Uses CrewAI `@CrewBase` pattern with 3 agents, 3 tasks, sequential process:

```python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

@CrewBase
class VCValidationCrew:
    """VC-style startup idea validation crew"""

    @agent
    def market_researcher(self) -> Agent: ...

    @agent
    def vc_analyst(self) -> Agent: ...

    @agent
    def report_writer(self) -> Agent: ...

    @task
    def market_research_task(self) -> Task: ...

    @task
    def vc_analysis_task(self) -> Task: ...

    @task
    def report_generation_task(self) -> Task: ...

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
```

### 9.3 Tools Implementation

Each tool in `tools/` is a CrewAI-compatible tool class:

**google_trends.py:**
- Uses `pytrends` (free) with SerpApi as fallback
- Extracts: interest_over_time, related_queries, interest_by_region
- Returns normalized trend data + "Breakout" signals

**reddit_analyzer.py:**
- Uses `praw` to search relevant subreddits
- Subreddits: `startups`, `SaaS`, `Entrepreneur`, `smallbusiness`, `indiehackers`, plus industry-specific ones
- Applies VADER sentiment to posts and comments
- Returns: top posts, sentiment distribution, key pain points mentioned

**web_searcher.py:**
- Uses SerperDev API for Google search
- Searches for: competitors, market size data, recent funding, industry news
- Returns: structured search results with relevance scoring

**website_scraper.py:**
- Uses `httpx` + `BeautifulSoup` for static sites
- Falls back to `playwright` for JS-heavy sites
- Extracts: title, meta, headings, body text, tech signals
- Returns: site analysis summary

**file_analyzer.py:**
- PDF: uses `pymupdf4llm` for Markdown extraction
- PPTX: uses `python-pptx` to extract slide text
- Returns: extracted content + slide-by-slide breakdown (for pitch decks)

### 9.4 Tone System

The `feedback_tone` field controls the Report Writer agent's system prompt:

**Brutally Honest:**
> "You are a ruthless VC partner who has seen 10,000 terrible pitches. You identify fatal flaws FIRST. You don't soften language. If the idea is bad, say it's bad and explain exactly why. Use phrases like 'This is a red flag', 'I've seen this fail 100 times', 'No serious investor would fund this because...' But always back up your harshness with data and logic. Never be mean for the sake of being mean — be mean because the founder NEEDS to hear this before wasting their life savings."

**Constructive:**
> "You are a supportive but honest VC mentor. You lead with strengths, then address weaknesses with specific improvement suggestions. For every problem you identify, propose at least one alternative approach. Use phrases like 'This could be stronger if...', 'Consider pivoting to...', 'The data suggests an opportunity in...' Your goal is to help the founder improve their idea, not crush their spirit."

**Roast Me:**
> "You are a comedy roast writer who also happens to be a brilliant VC. Your feedback is savage, funny, and peppered with analogies and pop culture references. But underneath every joke is a genuine insight. You might say things like 'This business model is like a screen door on a submarine — technically functional but fundamentally confused' or 'Your TAM calculation has the same energy as me estimating my dating pool by counting everyone on Earth.' But always end sections with the actual actionable takeaway."

---

## 10. Masumi Payment Service Setup

### 10.1 Quick Start (Docker — Recommended)

```bash
# Clone the dev quickstart (includes Payment + Registry + DB)
git clone https://github.com/masumi-network/masumi-services-dev-quickstart.git
cd masumi-services-dev-quickstart

# Copy env template
cp .env.example .env
# Edit .env — add your Blockfrost API key

# Start everything
docker compose up -d

# Payment Service available at:
#   API docs: http://localhost:3001/docs
#   Admin:    http://localhost:3001/admin
```

### 10.2 Agent Registration

After the Payment Service is running:

1. **Top up selling wallet** with Test-ADA from https://dispenser.masumi.network/
2. **Create API key**: `GET /api-key/` on Payment Service
3. **Register agent**: `POST /registry/` with agent metadata (name, description, API URL, pricing)
4. **Wait for registration** (~5 minutes on Preprod)
5. **Copy agent identifier** from `GET /registry/` response
6. **Update `.env`** with `AGENT_IDENTIFIER`, `PAYMENT_API_KEY`, `SELLER_VKEY`

### 10.3 Listing on Sokosumi

Follow: https://docs.masumi.network/documentation/how-to-guides/list-agent-on-sokosumi

---

## 11. Resource Links

### Masumi Documentation
- Masumi Docs: https://docs.masumi.network/documentation
- MIP-003 API Standard: https://docs.masumi.network/mips/_mip-003
- CrewAI Quickstart Template: https://github.com/masumi-network/crewai-masumi-quickstart-template
- Agentic Service Wrapper: https://github.com/masumi-network/agentic-service-wrapper
- masumi-crewai PyPI: https://pypi.org/project/masumi-crewai/
- Coding Mentor Example Agent: https://github.com/masumi-network/crewai-coding-mentor-agent
- Masumi Network GitHub: https://github.com/masumi-network
- Dev Quickstart (Docker): https://github.com/masumi-network/masumi-services-dev-quickstart
- Sokosumi Marketplace: https://sokosumi.com
- List Agent on Sokosumi: https://docs.masumi.network/documentation/how-to-guides/list-agent-on-sokosumi
- Masumi DeepWiki: https://deepwiki.com/masumi-network/masumi-docs

### CrewAI Documentation
- CrewAI Docs: https://docs.crewai.com
- CrewAI Quickstart: https://docs.crewai.com/en/quickstart
- CrewAI Tools: https://docs.crewai.com/en/core-concepts/tools

### Data Source APIs
- pytrends (Google Trends): https://github.com/GeneralMills/pytrends (archived)
- SerpApi (Google Search + Trends): https://serpapi.com
- SerperDev (Google Search): https://serper.dev
- PRAW (Reddit): https://praw.readthedocs.io
- Reddit API: https://www.reddit.com/dev/api
- pymupdf4llm (PDF extraction): https://pypi.org/project/pymupdf4llm/
- python-pptx: https://python-pptx.readthedocs.io
- VADER Sentiment: https://github.com/cjhutto/vaderSentiment

### Competitor Research
- AI CoFounder: https://aicofounder.com
- DimeADozen.ai: https://www.dimeadozen.ai
- IdeaProof: https://ideaproof.io
- ValidatorAI: https://validatorai.com

### VC Frameworks
- Sequoia Business Plan Framework: https://sequoiacap.com/article/writing-a-business-plan/
- YC Application Guide: https://www.ycombinator.com/howtoapply

---

## 12. Development Workflow

### Phase 1: Foundation (Week 1)
- [ ] Clone masumi quickstart template
- [ ] Set up project structure per Section 8
- [ ] Implement MIP-003 endpoints in `main.py`
- [ ] Define input schema (Section 4.1)
- [ ] Set up `.env` with all API keys
- [ ] Basic health check tests

### Phase 2: Tools (Week 2)
- [ ] Build Google Trends tool
- [ ] Build Reddit analyzer tool
- [ ] Build web search tool
- [ ] Build website scraper tool
- [ ] Build PDF/PPTX file analyzer tool
- [ ] Unit tests for all tools

### Phase 3: Analysis Engine (Week 3)
- [ ] Implement Sequoia 10-point framework
- [ ] Implement TAM/SAM/SOM estimation
- [ ] Implement scoring matrix
- [ ] Implement moat analysis
- [ ] Implement tone system (3 prompts)

### Phase 4: CrewAI Integration (Week 4)
- [ ] Define 3 agents in crew_definition.py
- [ ] Define 3 sequential tasks
- [ ] Wire tools to market researcher agent
- [ ] Test full crew pipeline end-to-end
- [ ] Pydantic output validation

### Phase 5: Masumi Integration & Deployment (Week 5)
- [ ] Set up Masumi Payment Service (Docker)
- [ ] Register agent on Preprod
- [ ] Test full payment → job → result flow
- [ ] Deploy to hosting (Railway, AWS, etc.)
- [ ] List on Sokosumi marketplace
- [ ] Switch to Mainnet when ready
