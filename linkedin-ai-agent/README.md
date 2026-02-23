# LinkedIn AI Content Agent

Automate your LinkedIn posts from your GitHub repositories using AI.

## Features

- **RAG-powered analysis**: Understands your codebase using embeddings and semantic search
- **Git-aware**: Prioritizes recent commits for fresh content
- **Adaptive posts**: Automatically adjusts length and style based on content
- **Code snippets**: Includes relevant code in posts when appropriate
- **Telegram bot**: Manage everything through Telegram commands
- **Daily automation**: Scheduled posts at your preferred time
- **LinkedIn integration**: One-click publishing to LinkedIn

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
OPENAI_API_KEY=your_openai_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
```

### 3. Get your API keys

#### OpenAI
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add to `.env` as `OPENAI_API_KEY`

#### Telegram Bot
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the instructions
3. Copy the token and add to `.env` as `TELEGRAM_BOT_TOKEN`

#### LinkedIn (Optional - for auto-posting)
1. Go to [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
2. Create a new app
3. Add the "Share on LinkedIn" and "Sign In with LinkedIn" products
4. Copy Client ID and Client Secret to `.env`
5. Add `http://localhost:8080/callback` as a redirect URL

### 4. Run the bot

```bash
cd src
python -m bot.main
```

## Usage

### Telegram Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and instructions |
| `/connect <url>` | Connect a public GitHub repository |
| `/disconnect` | Remove connected repository |
| `/time <HH:MM>` | Set daily posting time (24-hour format) |
| `/cleartime` | Disable automatic daily posts |
| `/generate` | Generate a LinkedIn post now |
| `/refresh` | Re-index your repository |
| `/auth` | Connect your LinkedIn account |
| `/authstatus` | Check LinkedIn connection status |
| `/deauth` | Disconnect LinkedIn |
| `/status` | View your current configuration |
| `/help` | Show help message |

### Approving Posts

When the bot sends you a draft, reply with any of these to publish:
- `post`
- `yes`
- `go`
- `ship`

### Example Workflow

1. Start chat with your bot on Telegram
2. `/connect https://github.com/your-username/your-repo`
3. `/time 09:00` (set daily post time)
4. `/auth` (connect LinkedIn)
5. `/generate` (test it out!)
6. Reply `post` to publish

## CLI Usage (Without Telegram)

You can also use the CLI directly:

```bash
cd src

# Index and generate a post
python main.py --repo https://github.com/user/repo --index

# Generate with specific focus
python main.py --repo https://github.com/user/repo --focus "authentication"

# Generate multiple variations
python main.py --repo https://github.com/user/repo --variations 3

# Force refresh repository
python main.py --repo https://github.com/user/repo --refresh
```

## Architecture

```
linkedin-ai-agent/
├── src/
│   ├── rag/                 # RAG Pipeline
│   │   ├── loader.py        # GitHub repo fetching
│   │   ├── chunker.py       # Code chunking
│   │   ├── embedder.py      # OpenAI embeddings
│   │   ├── store.py         # ChromaDB storage
│   │   └── retriever.py     # Semantic search
│   ├── generator/           # Content Generation
│   │   └── post_generator.py
│   ├── bot/                 # Telegram Bot
│   │   ├── main.py          # Entry point
│   │   ├── handlers.py      # Message handlers
│   │   ├── config.py        # User config storage
│   │   ├── approval.py      # Post approval flow
│   │   └── commands/        # Bot commands
│   ├── linkedin/            # LinkedIn Integration
│   │   ├── oauth.py         # OAuth flow
│   │   └── poster.py        # Post publishing
│   ├── scheduler/           # Automation
│   │   └── cron.py          # Daily scheduler
│   └── main.py              # CLI entry point
├── docs/
│   └── MVP-PLAN.md          # Full project plan
├── .env.example
├── requirements.txt
└── README.md
```

## Tech Stack

- **Python 3.10+**
- **LangChain** - RAG and agent orchestration
- **OpenAI** - Embeddings and content generation
- **ChromaDB** - Local vector storage
- **GitPython** - Repository operations
- **python-telegram-bot** - Telegram interface
- **APScheduler** - Daily scheduling
- **LinkedIn API** - Post publishing

## How It Works

1. **Connect**: You provide a GitHub repository URL
2. **Index**: The bot clones your repo and creates searchable embeddings
3. **Analyze**: Each day, it checks for new commits and interesting code
4. **Generate**: AI creates a LinkedIn post about your work
5. **Review**: You receive a draft on Telegram
6. **Publish**: Reply to approve and post to LinkedIn

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT

## Roadmap

- [x] Phase 1: RAG Pipeline (CLI)
- [x] Phase 2: Telegram Bot
- [x] Phase 3: LinkedIn Integration + Automation
- [ ] WhatsApp integration
- [ ] Private repo support
- [ ] Multiple repos per user
- [ ] Post analytics
- [ ] Web dashboard
