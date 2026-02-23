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

---

## Future Enhancements (Post-MVP)

- WhatsApp integration
- Private repo support (GitHub OAuth)
- Multiple repos per user
- Post scheduling (queue posts)
- Edit post via Telegram reply
- Analytics (track post performance)
- Multiple LLM support (Claude, Gemma)
- Web dashboard
