# Idea Validation Agent

A human-in-the-loop AI agent that validates any startup idea through a short back-and-forth. Built with **FastAPI + CrewAI**, wrapped in the **Masumi MIP-003 API standard**, and designed for the **Sokosumi marketplace**.

## How It Works

1. **You submit a single idea** (plus an optional feedback tone).
2. **The agent does a quick scoping pass** to infer the industry, likely audience, and obvious competitors.
3. **It asks you 3–5 dynamic follow-up questions** via MIP-003 `/provide_input`, generated from that scoping read.
4. **It runs a full deep-research crew** — Google Trends, web search, news, GitHub ecosystem signals, YouTube discourse, Similarweb, website scraping — then applies VC frameworks (Sequoia 10-point, TAM/SAM/SOM, YC filter, moat).
5. **It returns a draft report** and asks you to approve or request changes.
6. **Loop until you approve.** Each round of feedback rewrites the report.

## Features

- **Human-in-the-loop by default**: the agent pauses and asks the user before committing to a full report
- **Dynamic clarifying questions**: generated per idea, not from a fixed form
- **Real-time market research**: Google Trends, web search, news, GitHub ecosystem, YouTube discourse, Similarweb, web scraping
- **VC-grade evaluation**: Sequoia 10-point, TAM/SAM/SOM, YC filter, moat, unit economics
- **Multiple feedback tones**: brutally honest, constructive, or roast-me
- **MIP-003 compliant** and ready for Masumi / Sokosumi
- **Blockchain payments** via Cardano (Preprod/Mainnet)

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Install Playwright browsers (for website scraping)
playwright install chromium
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

**Required API Keys**:
- `ANTHROPIC_API_KEY` - Get from https://console.anthropic.com
- `SERPAPI_API_KEY` OR `SERPER_API_KEY` - Get from https://serpapi.com or https://serper.dev
- `PAYMENT_SERVICE_URL` + `PAYMENT_API_KEY` + `AGENT_IDENTIFIER` - From Masumi Payment Service admin
  - **Note:** Pricing is configured in the Payment Service admin interface, not in code

**Optional (but recommended)**:
- `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` - Create app at https://www.reddit.com/prefs/apps (requires approval)
- `NEWSAPI_API_KEY` - For market/news momentum via https://newsapi.org
- `GITHUB_TOKEN` - For higher-rate GitHub ecosystem searches via https://github.com/settings/tokens
- `YOUTUBE_API_KEY` - For creator discourse via https://developers.google.com/youtube/v3/getting-started
- `SIMILARWEB_API_KEY` - For website traffic/rank benchmarking via https://developers.similarweb.com

**Placeholder env vars already included for future premium diligence**:
- `CRUNCHBASE_API_KEY`
- `GOOGLE_ADS_DEVELOPER_TOKEN`
- `GOOGLE_ADS_CLIENT_ID`
- `GOOGLE_ADS_CLIENT_SECRET`
- `GOOGLE_ADS_REFRESH_TOKEN`
- `GOOGLE_ADS_LOGIN_CUSTOMER_ID`

See `.env.example` for full configuration details.

### 3. Run Locally (Development Mode)

```bash
# Run in API mode (recommended)
python main.py

# Or with masumi CLI
masumi run main.py

# For testing without payments
masumi run main.py --standalone --input '{...}'
```

The server will start on http://localhost:8080

### 4. Test the Agent

```bash
# Check availability
curl http://localhost:8080/availability

# Get input schema
curl http://localhost:8080/input_schema

# Submit a validation job
curl -X POST http://localhost:8080/start_job \
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

# Check job status
curl http://localhost:8080/status?job_id=<job_id_from_above>
```

## Project Structure

```
vc-validation-agent/
├── agent.py                     # Main agent logic - process_job function
├── main.py                      # Entry point - runs Masumi server
├── crew_definition.py           # CrewAI crew (3 agents, 3 tasks)
│
├── config/
│   ├── settings.py              # Pydantic settings from .env
│   └── __init__.py
│
├── schemas/
│   ├── input_schema.py          # MIP-003 input schema definition
│   ├── output_schema.py         # ValidationReport Pydantic models
│   └── __init__.py
│
├── tools/
│   ├── google_trends.py         # Google Trends research tool
│   ├── reddit_analyzer.py       # Reddit sentiment analysis
│   ├── web_searcher.py          # Web search (SerperDev/SerpApi)
│   ├── news_intelligence.py     # NewsAPI-based market/news signal
│   ├── github_ecosystem.py      # GitHub repo/activity signal
│   ├── youtube_signal.py        # YouTube creator discourse signal
│   ├── similarweb_analysis.py   # Similarweb traffic/rank benchmark
│   ├── website_scraper.py       # Website scraping + analysis
│   ├── file_analyzer.py         # PDF/PPTX pitch deck analyzer
│   └── __init__.py
│
├── analysis/
│   ├── market_sizing.py         # TAM/SAM/SOM framework
│   ├── frameworks.py            # Sequoia, YC, moat analysis
│   ├── scoring.py               # Scoring matrix computation
│   └── __init__.py
│
├── prompts/
│   ├── market_researcher.md     # System prompt for research agent
│   ├── vc_analyst.md            # System prompt for VC analysis agent
│   ├── report_writer_brutal.md  # Brutally honest tone
│   ├── report_writer_constructive.md  # Constructive tone
│   └── report_writer_roast.md   # Roast mode tone
│
├── requirements.txt
├── .env.example
├── .env                         # Your config (gitignored)
└── README.md                    # This file
```

## How It Works

### 3-Agent Crew Architecture

1. **Market Researcher Agent**
   - Runs Google Trends analysis
   - Searches Reddit for sentiment
   - Searches web for competitors and market data
   - Pulls recent media coverage
   - Measures GitHub ecosystem activity for technical markets
   - Captures YouTube discourse
   - Benchmarks traffic/rank if Similarweb is configured
   - Scrapes website if URL provided
   - Analyzes pitch deck if file provided
   - Returns structured research findings

2. **VC Analyst Agent**
   - Applies Sequoia 10-point framework
   - Calculates TAM/SAM/SOM estimates
   - Runs YC 5-question filter
   - Analyzes competitive moats
   - Generates 10-dimension scoring matrix
   - Determines verdict and confidence level

3. **Report Writer Agent**
   - Synthesizes all analysis
   - Applies selected feedback tone (Brutal/Constructive/Roast)
   - Generates comprehensive markdown report
   - Includes actionable next steps

### Input Schema

The agent accepts these fields:

**Required**:
- `idea_description` - Your startup idea (min 50 chars)
- `founder_stage` - What stage you're at
- `industry` - Industry vertical
- `goal` - What you want to achieve
- `feedback_tone` - Brutally Honest / Constructive / Roast Me

**Optional**:
- `target_audience` - Who your customers are
- `business_model` - How you'll make money
- `team_size` - How big your team is
- `existing_traction` - Any users/revenue
- `competitors` - Known competitors
- `unique_advantage` - Your unfair advantage
- `website_url` - Landing page to analyze
- `pitch_deck_file` - Pitch deck URL (PDF/PPTX)

See full schema with `GET /input_schema`

### Output Format

The agent returns a validation report containing:

- **Executive Summary** - Investment thesis
- **Verdict** - STRONG OPPORTUNITY / PROMISING / NEEDS WORK / HIGH RISK / DO NOT PURSUE
- **Viability Score** - 0-100 overall score
- **10-Dimension Scoring Matrix** - Each dimension scored 1-10 with reasoning
- **Market Analysis** - TAM/SAM/SOM, trends, competitors
- **Expanded Evidence Layer** - News, ecosystem, traffic, and creator signals when configured
- **SWOT Analysis** - Strengths, Weaknesses, Opportunities, Threats
- **Critical Risks** - With severity and mitigation strategies
- **Actionable Next Steps** - Prioritized roadmap
- **Website/Pitch Deck Feedback** - If provided

## Deployment to Masumi Network

### Prerequisites

1. **Set up Masumi Payment Service**

```bash
# Clone dev quickstart
git clone https://github.com/masumi-network/masumi-services-dev-quickstart.git
cd masumi-services-dev-quickstart

# Configure and start
cp .env.example .env
# Edit .env with your Blockfrost API key
docker compose up -d
```

Payment Service will be available at http://localhost:3001

2. **Get Test-ADA for Preprod**

Visit https://dispenser.masumi.network/ and fund your selling wallet.

3. **Register Your Agent**

```bash
# Create API key
curl http://localhost:3001/api-key/

# Register agent (replace with your details)
curl -X POST http://localhost:3001/registry/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "VC Validation Agent",
    "description": "AI agent that validates startup ideas like a VC partner",
    "api_url": "http://your-deployment-url.com",
    "price_amount": "5000000",
    "price_unit": "lovelace"
  }'

# Wait ~5 minutes for registration to complete
# Check status
curl http://localhost:3001/registry/
```

4. **Update .env with Registration Details**

```bash
AGENT_IDENTIFIER=your_agent_identifier_from_registry
PAYMENT_API_KEY=your_payment_api_key
SELLER_VKEY=your_wallet_vkey
```

5. **Deploy Agent**

Deploy to your preferred platform:
- Railway
- AWS Lambda
- Google Cloud Run
- Your own server

Ensure the deployment is publicly accessible and update `api_url` in registry.

6. **List on Sokosumi Marketplace**

Follow: https://docs.masumi.network/documentation/how-to-guides/list-agent-on-sokosumi

## API Endpoints

The agent implements MIP-003 standard endpoints:

- `GET /availability` - Health check
- `GET /input_schema` - Returns input schema
- `POST /start_job` - Submit validation job
- `GET /status?job_id=xxx` - Check job status
- `POST /provide_input` - Provide additional input (HITL)

## Troubleshooting

### "Missing API key" errors

Ensure all required keys are set in `.env`:
- `ANTHROPIC_API_KEY`
- `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET`
- `SERPER_API_KEY` or `SERPAPI_API_KEY`

### Rate limit errors

Research tools may hit API rate limits. The agent gracefully degrades - it will include what it found and note what failed.

### Payment not detected

Check:
1. Wallet is funded on correct network (Preprod vs Mainnet)
2. Payment amount matches `PAYMENT_AMOUNT` in .env
3. `AGENT_IDENTIFIER` matches registered agent

## Resources

### Masumi Documentation
- [Masumi Docs](https://docs.masumi.network/documentation)
- [MIP-003 API Standard](https://docs.masumi.network/mips/_mip-003)
- [Quickstart Template](https://github.com/masumi-network/crewai-masumi-quickstart-template)

### API Keys
- [Anthropic Claude](https://console.anthropic.com)
- [Reddit API](https://www.reddit.com/prefs/apps)
- [SerperDev](https://serper.dev)
- [SerpApi](https://serpapi.com)

### VC Frameworks
- [Sequoia Business Plan](https://sequoiacap.com/article/writing-a-business-plan/)
- [YC Application Guide](https://www.ycombinator.com/howtoapply)

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
- Open an issue on GitHub
- Join Masumi Discord: https://discord.gg/masumi
- Check PRD: See `../files/PRD_VC_VALIDATION_AGENT.md` for complete specifications

---

**Built with**: FastAPI, CrewAI, Claude, Masumi Network

**Accepts payments in**: Cardano (ADA/USDM)

**Listed on**: [Sokosumi Marketplace](https://sokosumi.com)
