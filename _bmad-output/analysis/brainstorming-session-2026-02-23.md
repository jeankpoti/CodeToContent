# Brainstorming Session: LinkedIn AI Content Agent

**Date:** 2026-02-23
**Facilitator:** Carson (Brainstorming Coach)
**Project:** LinkedIn AI Content Agent (Open Source)

---

## Session Overview

**Topic:** MVP Scope for LinkedIn AI Content Agent
**Goals:**
- Define minimum viable product for open source release
- Learn AI engineering (RAG, agents, function calling)
- Ship fast with phased weekend builds

**Target Users:** Developers & creators who want to automate LinkedIn content

---

## Techniques Used

1. **Question Storming** - 47 questions explored to define problem space
2. **First Principles Thinking** - Strip to essential features only
3. **Resource Constraints** - Weekend-sized build phases

---

## Key Questions Explored (47 Total)

### Tech Stack Questions
| # | Question | Decision |
|---|----------|----------|
| 1 | Which LLM? | OpenAI (MVP) |
| 2 | LangChain or LlamaIndex? | LangChain |
| 3 | Vector DB: Pinecone or ChromaDB? | ChromaDB (local, simpler) |
| 4 | How to make stack choices easy for contributors? | Use popular/documented tools |
| 5-10 | Should we abstract the LLM layer from Day 1? | No, visible wiring for learning |

### User Flow Questions
| # | Question | Decision |
|---|----------|----------|
| 11 | GitHub repo URL only or local folders too? | Public URLs only (MVP) |
| 12 | Connect once and poll, or manual trigger? | Daily cron + manual /generate |
| 13 | Public repos only or private too? | Public only (skip OAuth) |
| 14 | Whole repo or specific folders? | Whole repo, smart chunking |
| 15 | What if repo is huge? | Chunk smartly, limit scope |
| 16 | What triggers daily post? | Cron at user's chosen time |
| 17 | Git diff analysis or full repo context? | Both (prioritize diff) |
| 18 | One post style or multiple templates? | Adaptive (AI picks) |
| 19 | How avoid repetitive posts? | Content quality logic |
| 20 | Post format: text only or with code? | Include code snippets |

### Telegram/Delivery Questions
| # | Question | Decision |
|---|----------|----------|
| 21 | Send draft for approval or auto-post? | Draft to Telegram |
| 22 | How do they edit the post? | Future enhancement |
| 23 | Reply "approve" on WhatsApp or link to web UI? | Reply in Telegram |
| 24 | What if they're offline? | Queue posts |
| 25 | Daily posts? Weekly? On-demand? | User picks time |

### Onboarding Questions
| # | Question | Decision |
|---|----------|----------|
| 26 | How does user first connect? | Telegram bot command |
| 27 | Paste GitHub URL into Telegram bot? | Yes, /connect <url> |
| 28 | OAuth for GitHub or just public URLs? | Public URLs only |
| 29 | How connect LinkedIn account? | OAuth (required) |
| 30 | Store preferences where? | Per-chat config file |

### Approval Flow Questions
| # | Question | Decision |
|---|----------|----------|
| 31 | What time does cron run? | User picks |
| 32 | What if nothing new to post? | Fallback to repo highlights |
| 33 | Post length: short or long? | Adaptive |
| 34 | User replies "post" exact word? | Accept variations (yes/go/ship) |
| 35 | Can they reply "edit: change X"? | Future enhancement |
| 36 | What if they ignore it? | No timeout for MVP |

### Architecture Questions
| # | Question | Decision |
|---|----------|----------|
| 37-40 | User database needed? | No, Telegram chat ID = user |
| 41-44 | Timezone logic? | Pull from Telegram |
| 45-47 | Weekend build order? | RAG → Bot → LinkedIn |

---

## First Principles Analysis

**Challenge:** Are all 12 features truly MUST-have?

### Features Challenged

| Feature | Challenge | Verdict |
|---------|-----------|---------|
| User picks time | Could default to 9am UTC | **MUST** - essential UX |
| Fallback to repo highlights | Could skip post if no commits | **MUST** - handles no-commit days |
| All others | Already minimal | **MUST** - all kept |

**Result:** All 12 features confirmed as essential for MVP value.

---

## Resource Constraints Applied

### Constraint #1: Weekend Build Challenge

**Question:** If you only had one weekend, what's the first vertical slice?

**Answer:** RAG Pipeline (Option C)
- Clone repo → chunk code → embed → store → retrieve → generate post
- Test post quality before adding delivery

### Constraint #2: Only 3 Extra Libraries

Beyond LangChain + OpenAI:
1. **ChromaDB** - Local vector store
2. **GitPython** - Repo operations
3. **python-telegram-bot** - Messaging

### Constraint #3: One User Only (MVP)

**Simplifications enabled:**
- No user database
- No signup/auth flow
- Telegram chat ID = user identity
- Per-chat config file storage
- Hardcode user's timezone from Telegram

---

## Final MVP Flow

```
┌─────────────────────────────────────────────────────────┐
│  NO BACKEND AUTH - TELEGRAM IS THE USER SYSTEM         │
├─────────────────────────────────────────────────────────┤
│  User opens Telegram bot                                │
│  └→ Chat ID = User identity                            │
│  └→ /connect <github-url> → Store in chat context      │
│  └→ /auth → LinkedIn OAuth flow → Store token          │
│  └→ /time 9:00 → Store preference (use phone TZ)       │
├─────────────────────────────────────────────────────────┤
│  Daily cron per chat:                                   │
│  └→ Check user's preferred time (in their TZ)          │
│  └→ Generate → Send draft → Wait for approval          │
└─────────────────────────────────────────────────────────┘
```

---

## Decision Rationale Summary

| Decision | Why |
|----------|-----|
| Python over TypeScript | Better AI/ML ecosystem, learning focus |
| ChromaDB over Pinecone | Local, no cloud setup, simpler for open source |
| Telegram over web UI | No frontend needed, instant mobile access |
| No user accounts | Telegram handles identity, reduces complexity |
| Public repos only | Skip GitHub OAuth for MVP |
| Adaptive post length | Let AI decide, less config for users |
| RAG pipeline first | Core value, testable in isolation |

---

## Implementation Phases

### Phase 1: RAG Pipeline (Weekend 1) - COMPLETED
- Repo fetching with GitPython
- Code chunking with LangChain
- Embeddings with OpenAI
- Storage with ChromaDB
- Post generation with LLM
- CLI interface

### Phase 2: Telegram Bot (Weekend 2) - PENDING
- Bot commands (/connect, /time, /generate)
- Per-chat configuration
- Draft delivery

### Phase 3: LinkedIn + Automation (Weekend 3) - PENDING
- LinkedIn OAuth
- Approval flow
- Daily cron scheduler
- Post publishing

---

## Session Metrics

- **Total Questions Generated:** 47
- **Techniques Used:** 3
- **Features Defined:** 12 (all MUST-have)
- **Phases Planned:** 3 weekends
- **Phase 1 Status:** COMPLETED

---

## Files Created in Session

### Project Documentation
- `linkedin-ai-agent/docs/MVP-PLAN.md`
- `_bmad-output/analysis/brainstorming-session-2026-02-23.md`

### Phase 1 Code (Completed)
- `linkedin-ai-agent/src/rag/loader.py`
- `linkedin-ai-agent/src/rag/chunker.py`
- `linkedin-ai-agent/src/rag/embedder.py`
- `linkedin-ai-agent/src/rag/store.py`
- `linkedin-ai-agent/src/rag/retriever.py`
- `linkedin-ai-agent/src/generator/post_generator.py`
- `linkedin-ai-agent/src/main.py`
- `linkedin-ai-agent/requirements.txt`
- `linkedin-ai-agent/.env.example`
- `linkedin-ai-agent/README.md`
- `linkedin-ai-agent/.gitignore`
