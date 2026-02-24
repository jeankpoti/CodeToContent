# LinkedIn AI Content Agent

Automate your LinkedIn posts from your GitHub repositories using an AI agent that researches trends, analyzes your code, and learns what content performs best.

## Features

### Core Features
- **RAG-powered analysis**: Understands your codebase using embeddings and semantic search
- **Git-aware**: Prioritizes recent commits for fresh content
- **Adaptive posts**: Automatically adjusts length and style based on content
- **Code snippets**: Includes relevant code in posts when appropriate
- **Telegram bot**: Manage everything through Telegram commands
- **Daily automation**: Scheduled posts at your preferred time
- **LinkedIn integration**: One-click publishing to LinkedIn

### AI Agent Capabilities
- **Multi-Repo Selection**: Connect up to 5 repos - agent decides which has the best content today
- **Trend Research**: Fetches trending topics from HackerNews (free!) and Twitter/X (optional)
- **Trend Matching**: Automatically matches trending topics to relevant code in your repos
- **Engagement Learning**: Tracks LinkedIn metrics and learns what content performs best
- **Autonomous Reasoning**: ReAct agent that thinks step-by-step about content strategy
- **Explainable Decisions**: Use `/why` to understand why the agent made specific choices

## Quick Start

### 1. Install dependencies

```bash
cd linkedin-ai-agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# Required
OPENAI_API_KEY=your_openai_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# Optional - for LinkedIn posting
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret

# Optional - for Twitter trends (HackerNews is free!)
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
```

### 3. Get your API keys

#### OpenAI (Required)
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add to `.env` as `OPENAI_API_KEY`

#### Telegram Bot (Required)
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the instructions
3. Copy the token and add to `.env` as `TELEGRAM_BOT_TOKEN`

#### LinkedIn (Optional - for auto-posting)
1. Go to [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
2. Create a new app
3. Add the "Share on LinkedIn" and "Sign In with LinkedIn" products
4. Copy Client ID and Client Secret to `.env`
5. Add `http://localhost:8080/callback` as a redirect URL

#### Twitter (Optional - HackerNews trends are free!)
1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a project and get Bearer Token
3. Add to `.env` as `TWITTER_BEARER_TOKEN`

### 4. Run the bot

```bash
cd src
python -m bot.main
```

## Usage

### Telegram Commands

#### Repository Management
| Command | Description |
|---------|-------------|
| `/addrepo <url>` | Add a GitHub repository (up to 5) |
| `/repos` | List all connected repositories |
| `/removerepo <url>` | Remove a repository |
| `/refresh` | Re-index all repositories |

#### Content Generation
| Command | Description |
|---------|-------------|
| `/generate` | Generate a LinkedIn post using the AI agent |
| `/trends` | View current developer trends (HackerNews + Twitter) |

#### Learning & Insights
| Command | Description |
|---------|-------------|
| `/insights` | View what content performs best for you |
| `/why` | Explain why the last post was generated |
| `/stats <likes> <comments>` | Manually input post metrics for learning |

#### Scheduling
| Command | Description |
|---------|-------------|
| `/time <HH:MM>` | Set daily posting time (24-hour format) |
| `/cleartime` | Disable automatic daily posts |

#### LinkedIn
| Command | Description |
|---------|-------------|
| `/auth` | Connect your LinkedIn account |
| `/authstatus` | Check LinkedIn connection status |
| `/deauth` | Disconnect LinkedIn |

#### General
| Command | Description |
|---------|-------------|
| `/start` | Welcome message and instructions |
| `/status` | View your current configuration |
| `/help` | Show help message |

### Approving Posts

When the bot sends you a draft, reply with any of these to publish:
- `post`
- `yes`
- `go`
- `ship`

### Example Workflow

```
1. Start chat with your bot on Telegram
2. /addrepo https://github.com/your-username/project-1
3. /addrepo https://github.com/your-username/project-2
4. /time 09:00 (set daily post time)
5. /auth (connect LinkedIn)
6. /generate (the agent analyzes repos + trends!)
7. Reply 'post' to publish
8. /stats 50 10 (report engagement: 50 likes, 10 comments)
9. /insights (see what the agent learned)
```

## How the AI Agent Works

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTENT STRATEGIST AGENT                  │
│                    (LangChain ReAct Agent)                   │
├─────────────────────────────────────────────────────────────┤
│  REASONING LOOP:                                            │
│  1. "What trends are hot today?" → fetch_trends tool        │
│  2. "Which of my repos matches?" → analyze_repos tool       │
│  3. "What performed well before?" → get_insights tool       │
│  4. "Generate optimal post" → generate_post tool            │
│  5. "Track this for learning" → save to memory              │
└─────────────────────────────────────────────────────────────┘
```

### Agent Tools

| Tool | Purpose |
|------|---------|
| `fetch_trends` | Get trending topics from HackerNews/Twitter |
| `list_repos` | Get user's connected repositories |
| `analyze_repo` | Deep analysis of a repo's content potential |
| `compare_repos` | Rank repos by which has best content today |
| `match_trends` | Find code that matches trending topics |
| `search_code` | Semantic search in repositories |
| `get_post_history` | Past posts with engagement metrics |
| `get_insights` | Learned patterns about what works |
| `generate_post` | Create the LinkedIn post |

### Learning System

The agent learns from your post performance:

1. **Topic Performance**: Which topics get the most engagement
2. **Style Performance**: Posts with code vs without code
3. **Length Performance**: Short tips vs longer tutorials
4. **Repo Performance**: Which repos generate better content

Use `/stats <likes> <comments>` after each post to help the agent learn!

## CLI Usage (Without Telegram)

```bash
cd src

# Generate a post with the AI agent
python main.py --repo https://github.com/user/repo --agent

# Legacy mode (single repo, no agent)
python main.py --repo https://github.com/user/repo --index

# Generate with specific focus
python main.py --repo https://github.com/user/repo --focus "authentication"

# Generate multiple variations
python main.py --repo https://github.com/user/repo --variations 3
```

## Architecture

```
linkedin-ai-agent/
├── src/
│   ├── agent/                  # AI Agent (Phase 4)
│   │   ├── strategist.py       # ReAct agent orchestrator
│   │   ├── tools/              # Agent tools
│   │   │   ├── trends.py       # fetch_trends, get_all_trends
│   │   │   ├── repos.py        # list_repos, analyze_repo, compare_repos
│   │   │   ├── matching.py     # match_trends, search_code
│   │   │   ├── history.py      # get_post_history, get_insights
│   │   │   └── publisher.py    # generate_post
│   │   └── memory/             # Learning system
│   │       ├── database.py     # SQLite storage
│   │       └── learner.py      # Insight extraction
│   ├── trends/                 # Trend Sources
│   │   ├── hackernews.py       # FREE - No API key needed!
│   │   └── twitter.py          # Optional - requires API key
│   ├── rag/                    # RAG Pipeline
│   │   ├── loader.py           # GitHub repo fetching
│   │   ├── chunker.py          # Code chunking
│   │   ├── embedder.py         # OpenAI embeddings
│   │   ├── store.py            # ChromaDB storage
│   │   └── retriever.py        # Semantic search
│   ├── generator/              # Content Generation
│   │   └── post_generator.py   # LLM post creation
│   ├── bot/                    # Telegram Bot
│   │   ├── main.py             # Entry point
│   │   ├── handlers.py         # Message handlers
│   │   ├── config.py           # User config storage
│   │   ├── approval.py         # Post approval flow
│   │   └── commands/           # Bot commands
│   │       ├── repos.py        # /repos, /addrepo, /removerepo
│   │       ├── insights.py     # /insights, /trends, /why, /stats
│   │       ├── generate.py     # /generate, /refresh
│   │       ├── auth.py         # /auth, /authstatus
│   │       ├── time.py         # /time, /cleartime
│   │       └── connect.py      # /connect, /status (legacy)
│   ├── linkedin/               # LinkedIn Integration
│   │   ├── oauth.py            # OAuth flow
│   │   └── poster.py           # Post publishing
│   ├── scheduler/              # Automation
│   │   ├── cron.py             # Daily scheduler
│   │   └── metrics_fetcher.py  # Engagement tracking
│   └── main.py                 # CLI entry point
├── docs/
│   └── MVP-PLAN.md             # Full project plan
├── .env.example
├── requirements.txt
└── README.md
```

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Language | Python 3.10+ | Core implementation |
| Agent Framework | LangChain | ReAct agent + RAG |
| LLM | OpenAI GPT-4 | Content generation |
| Vector DB | ChromaDB | Local embeddings |
| Memory | SQLite | Post history + insights |
| Git | GitPython | Repository operations |
| Messaging | python-telegram-bot | User interface |
| Scheduling | APScheduler | Daily automation |
| Trends | HackerNews API (free) | Developer trends |

## Environment Variables

```env
# Required
OPENAI_API_KEY=your_openai_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# LinkedIn (optional)
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
LINKEDIN_REDIRECT_URI=http://localhost:8080/callback

# Twitter (optional - HackerNews is free!)
TWITTER_BEARER_TOKEN=your_twitter_bearer_token

# Agent settings (optional)
AGENT_MODE=true
AGENT_MAX_ITERATIONS=10
AGENT_TIMEOUT_SECONDS=60

# Storage paths (optional)
CHROMA_PERSIST_DIR=./chroma_db
REPOS_CACHE_DIR=./repos_cache
USER_CONFIGS_DIR=./user_configs
AGENT_DB_PATH=./agent_memory.db
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# Clone the repo
git clone https://github.com/your-username/linkedin-ai-agent.git
cd linkedin-ai-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your keys

# Run tests
python -m pytest tests/
```

## License

MIT

## Roadmap

- [x] Phase 1: RAG Pipeline (CLI)
- [x] Phase 2: Telegram Bot
- [x] Phase 3: LinkedIn Integration + Automation
- [x] Phase 4: AI Agent Architecture
  - [x] Multi-repo content selection (up to 5 repos)
  - [x] Trend research (HackerNews free + Twitter optional)
  - [x] Trend-to-code matching
  - [x] Engagement learning from metrics
  - [x] ReAct agent with autonomous reasoning
  - [x] Explainable decisions (/why command)
- [ ] WhatsApp integration
- [ ] Private repo support (GitHub OAuth)
- [ ] Web dashboard
- [ ] A/B testing for post styles
- [ ] Multi-language support

---

Built with LangChain, OpenAI, and Telegram.
