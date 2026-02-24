# LinkedIn AI Content Agent - MVP Plan

## Project Overview

**Name:** LinkedIn AI Content Agent (Open Source)
**Goal:** Automate daily LinkedIn posts from your GitHub repositories
**Target Users:** Developers & creators who want to build in public

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Language | Python | Core implementation |
| Agent Framework | LangChain | RAG + Agent orchestration |
| LLM | OpenAI | Content generation |
| Vector DB | ChromaDB | Local embeddings storage |
| Git Operations | GitPython | Clone/fetch repositories |
| Messaging | python-telegram-bot | User interface + delivery |
| Social | LinkedIn OAuth + API | Post publishing |

---

## User Flow

```
┌─────────────────────────────────────────────────────────┐
│  SETUP (One-time via Telegram):                        │
│  └→ User opens bot, sends /connect <github-url>        │
│  └→ User completes LinkedIn OAuth via /auth            │
│  └→ User sets preferred time via /time HH:MM           │
│  └→ Bot uses Telegram phone timezone automatically     │
├─────────────────────────────────────────────────────────┤
│  DAILY LOOP (Automated):                               │
│  └→ Cron triggers at user's chosen time                │
│  └→ Agent fetches git diff (or repo highlights)        │
│  └→ RAG retrieves relevant code context                │
│  └→ LLM generates post (adaptive length + code snippet)│
│  └→ Draft sent to Telegram chat                        │
├─────────────────────────────────────────────────────────┤
│  APPROVAL:                                             │
│  └→ User replies "post", "yes", "go", or "ship"        │
│  └→ Agent posts to LinkedIn                            │
│  └→ Confirmation sent back to Telegram                 │
└─────────────────────────────────────────────────────────┘
```

---

## MVP Features (All MUST-have)

| # | Feature | Description |
|---|---------|-------------|
| 1 | GitHub public URL input | User provides repo URL via Telegram command |
| 2 | LinkedIn OAuth | Connect LinkedIn account for posting |
| 3 | User picks daily time | Set preferred posting schedule |
| 4 | Daily cron trigger | Automated daily execution |
| 5 | Git diff analysis | Analyze recent commits for content |
| 6 | Fallback to repo highlights | If no commits, find interesting code |
| 7 | RAG context retrieval | Semantic search over codebase |
| 8 | Adaptive post length | Short tips vs longer features |
| 9 | Code snippets in post | Include actual code blocks |
| 10 | Telegram delivery | Send drafts via bot |
| 11 | Approval flow | Accept post/yes/go/ship replies |
| 12 | Post to LinkedIn | Publish approved content |

---

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| No signup/auth | Telegram chat ID = user identity | Simplicity, no backend DB needed |
| Timezone | Pull from Telegram user data | No manual timezone selection |
| Storage | Per-chat config file | Simple, no database required |
| Public repos only | Skip GitHub OAuth | Reduce complexity for MVP |

---

## Implementation Plan (Phased)

### Phase 1: RAG Pipeline (Weekend 1) - COMPLETED

**Goal:** Working post generator CLI

**Files created:**
- `src/rag/loader.py` - GitHub repo fetching with GitPython
- `src/rag/chunker.py` - Code file chunking logic
- `src/rag/embedder.py` - OpenAI embeddings generation
- `src/rag/store.py` - ChromaDB vector storage
- `src/rag/retriever.py` - Semantic search queries
- `src/generator/post_generator.py` - LangChain agent for post creation
- `src/main.py` - CLI entry point

**Deliverable:**
```bash
python src/main.py --repo https://github.com/user/repo
# Outputs: Generated LinkedIn post to terminal
```

### Phase 2: Telegram Bot (Weekend 2)

**Goal:** Bot that generates posts on command

**Files to create:**
- `src/bot/handlers.py` - Telegram command handlers
- `src/bot/commands/connect.py` - /connect command
- `src/bot/commands/time.py` - /time command
- `src/bot/commands/generate.py` - /generate command
- `src/bot/config.py` - Per-chat configuration storage
- `src/bot/main.py` - Bot entry point

**Commands:**
- `/start` - Welcome message + instructions
- `/connect <github-url>` - Store repo URL
- `/time HH:MM` - Set daily post time
- `/generate` - Manually trigger post generation

**Deliverable:** Working Telegram bot that generates posts on /generate

### Phase 3: LinkedIn + Automation (Weekend 3)

**Goal:** Full automated daily flow

**Files to create:**
- `src/linkedin/oauth.py` - OAuth flow handler
- `src/linkedin/poster.py` - Post publishing
- `src/bot/commands/auth.py` - /auth command
- `src/scheduler/cron.py` - Daily job scheduler
- `src/bot/approval.py` - Handle approval replies

**Commands:**
- `/auth` - Initiate LinkedIn OAuth
- Reply "post/yes/go/ship" - Approve and publish

**Deliverable:** Complete automated flow from repo to LinkedIn

### Phase 4: True AI Agent Architecture

**Goal:** Transform RAG pipeline into autonomous ReAct agent with decision-making capabilities

**Agent Capabilities:**
1. **Multi-Repo Selection** - Analyze 1-5 repos and decide which has best content today
2. **Trend Research** - Fetch trending topics from Twitter/X + HackerNews, match to code
3. **Engagement Learning** - Track LinkedIn metrics, learn what performs best, adapt strategy

**Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│                    CONTENT STRATEGIST AGENT                  │
│                    (LangChain ReAct Agent)                   │
├─────────────────────────────────────────────────────────────┤
│  REASONING LOOP:                                            │
│  1. "What trends are hot today?" → fetch_trends tool        │
│  2. "Which of my repos matches?" → analyze_repos tool       │
│  3. "What performed well before?" → get_history tool        │
│  4. "Generate optimal post" → generate_post tool            │
│  5. "Track this for learning" → log_post tool               │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
    ┌──────────┐       ┌──────────┐       ┌──────────┐
    │  TOOLS   │       │  MEMORY  │       │  SOURCES │
    ├──────────┤       ├──────────┤       ├──────────┤
    │ search   │       │ SQLite   │       │ Twitter  │
    │ analyze  │       │ - posts  │       │ HackerN. │
    │ compare  │       │ - metrics│       │ GitHub   │
    │ generate │       │ - insights       │ LinkedIn │
    │ post     │       └──────────┘       └──────────┘
    └──────────┘
```

**Agent Tools:**

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| `fetch_trends` | Get trending topics | source (twitter/hn) | List of trends with scores |
| `list_repos` | Get user's connected repos | chat_id | List of repo URLs |
| `analyze_repo` | Deep analysis of one repo | repo_url | Activity score, recent commits, interesting code |
| `compare_repos` | Rank repos by content potential | repo_urls[] | Ranked list with reasons |
| `match_trends` | Find code matching a trend | trend, repo_url | Relevant code snippets |
| `search_code` | Semantic search in repo | query, repo_url | Code chunks |
| `get_post_history` | Past posts & performance | chat_id, days | Posts with engagement metrics |
| `get_insights` | What content works best | chat_id | Learned patterns |
| `generate_post` | Create LinkedIn post | context, style | Post text |
| `post_to_linkedin` | Publish post | text, chat_id | Post URL |

**Memory Schema (SQLite):**

```sql
-- Track all posts
CREATE TABLE posts (
    id TEXT PRIMARY KEY,
    chat_id TEXT,
    repo_url TEXT,
    content TEXT,
    trend_matched TEXT,
    linkedin_post_id TEXT,
    created_at TIMESTAMP,
    posted_at TIMESTAMP
);

-- Track engagement metrics
CREATE TABLE metrics (
    post_id TEXT PRIMARY KEY,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    fetched_at TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES posts(id)
);

-- Store learned insights
CREATE TABLE insights (
    id TEXT PRIMARY KEY,
    chat_id TEXT,
    insight_type TEXT,  -- 'topic', 'style', 'time', 'repo'
    insight_key TEXT,   -- e.g., 'authentication', 'short-form'
    score REAL,         -- performance score
    sample_size INTEGER,
    updated_at TIMESTAMP
);
```

**Files to create:**
```
src/
├── agent/
│   ├── __init__.py
│   ├── strategist.py      # Main ReAct agent
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── trends.py      # fetch_trends (Twitter/HN)
│   │   ├── repos.py       # list_repos, analyze_repo, compare_repos
│   │   ├── matching.py    # match_trends, search_code
│   │   ├── history.py     # get_post_history, get_insights
│   │   └── publisher.py   # generate_post, post_to_linkedin
│   └── memory/
│       ├── __init__.py
│       ├── database.py    # SQLite operations
│       └── learner.py     # Insight extraction
├── trends/
│   ├── __init__.py
│   ├── twitter.py         # Twitter/X API
│   └── hackernews.py      # HackerNews API
```

**New Telegram Commands:**

| Command | Description |
|---------|-------------|
| `/repos` | List connected repositories |
| `/addrepo <url>` | Add another repository |
| `/removerepo <url>` | Remove a repository |
| `/insights` | View what the agent has learned |
| `/trends` | Show current trending topics |
| `/why` | Explain why last post was chosen |

**New Environment Variables:**
```env
# HackerNews: FREE, no API key needed!

# Twitter (OPTIONAL - only if you want Twitter trends too)
TWITTER_BEARER_TOKEN=your_twitter_bearer_token

# LinkedIn Marketing API (for engagement metrics)
LINKEDIN_MARKETING_ACCESS_TOKEN=your_marketing_token
```

**New Dependencies:**
```
tweepy>=4.14.0          # Twitter API
```

**Agent Reasoning Example:**
```
User triggers /generate at 9:00 AM

Agent thinks:
1. "Let me check what's trending today"
   → Calls fetch_trends("hackernews")
   → Returns: ["Rust memory safety", "AI code review", "WebAssembly"]

2. "What repos does this user have?"
   → Calls list_repos(chat_id)
   → Returns: ["repo-a", "repo-b", "repo-c"]

3. "Which repo matches these trends?"
   → Calls match_trends("AI code review", repos)
   → Returns: repo-b has code review automation

4. "What content style worked before?"
   → Calls get_insights(chat_id)
   → Returns: "short tips with code snippets get 2x engagement"

5. "Generate the post"
   → Calls generate_post(context=repo-b, style="short-tip", trend="AI code review")
   → Returns: Draft post

Agent returns draft to user via Telegram
```

**Deliverable:** Intelligent agent that autonomously decides content strategy

---

## Verification Plan

### Phase 1 Testing
1. Run CLI with a test GitHub repo
2. Verify code chunks are created correctly
3. Verify embeddings are stored in ChromaDB
4. Verify generated post is relevant and includes code snippet
5. Test with repos of different sizes

### Phase 2 Testing
1. Start Telegram bot locally
2. Test /connect with valid GitHub URL
3. Test /time with various time formats
4. Test /generate produces post in chat
5. Verify config persists between restarts

### Phase 3 Testing
1. Complete LinkedIn OAuth flow
2. Test approval replies (post, yes, go, ship)
3. Verify post appears on LinkedIn
4. Test cron triggers at correct time
5. End-to-end: Connect repo → Wait for cron → Approve → Verify LinkedIn post

### Phase 4 Testing
1. Memory Layer
   ```bash
   python -c "from src.agent.memory.database import Database; db = Database(); db.init()"
   # Verify tables created
   ```

2. Trend Fetching
   ```bash
   python -c "from src.trends.hackernews import get_trends; print(get_trends())"
   # Should return trending topics
   ```

3. Agent Reasoning
   ```bash
   python src/main.py --agent --repo https://github.com/user/repo --verbose
   # Watch agent reasoning steps in output
   ```

4. Full Agent Flow
   - `/addrepo` two repos via Telegram
   - `/generate` and verify agent picks best repo
   - Check `/why` explains the decision
   - Post and wait 24 hours
   - `/insights` to see learned patterns

5. Engagement Learning
   - Post multiple times over a week
   - Verify metrics are fetched from LinkedIn
   - Check that insights table is populated
   - Verify agent adapts recommendations

---

## Risk Mitigations

| Risk | Mitigation |
|------|------------|
| Twitter API costs | HackerNews is FREE (no API key), Twitter is optional |
| LinkedIn API approval | Provide manual `/stats <likes> <comments>` fallback |
| Agent loops/hangs | Set max iterations (10), timeout (60s) |
| Poor trend matching | Fallback to current RAG behavior if no match |

---

## Future Enhancements (Post-Phase 4)

- WhatsApp integration
- Private repo support (GitHub OAuth)
- Post scheduling (queue posts)
- Edit post via Telegram reply
- Multiple LLM support (Claude, Gemma)
- Web dashboard
- A/B testing for post styles
- Competitor analysis (what's working for others)
