# brAIn 🧠

A local, private MCP (Model Context Protocol) server that acts as your AI second brain. It persists knowledge across conversations — who you are, how you work, your projects, your team, your workflows — so every AI conversation starts with context instead of from scratch.

## Why

Every time you start a new AI chat, you lose context. You re-explain your setup, your team, your preferences. brAIn fixes this by running a local MCP server in Docker (or Finch) that remembers everything you tell it and lets any MCP-compatible AI assistant (Kiro, Claude, etc.) recall that knowledge.

**Everything stays on your machine. No cloud. No API keys for storage. Fully private.**

> Works with [Docker](https://www.docker.com/) or [Finch](https://runfinch.com/) (just replace `docker` with `finch` in the commands below).

## How It Works

```
┌─────────────────────────────────────────────────────┐
│                   AI Assistant                       │
│              (Kiro, Claude, etc.)                    │
└──────────────────────┬──────────────────────────────┘
                       │ MCP Protocol (stdio/SSE)
                       ▼
┌─────────────────────────────────────────────────────┐
│                brAIn MCP Server                      │
│             (Docker/Finch container)                  │
│                                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │   Memory     │  │   Semantic   │  │  Profile   │ │
│  │   Manager    │  │   Search     │  │  Manager   │ │
│  └──────┬──────┘  └──────┬───────┘  └─────┬──────┘ │
│         │                │                 │         │
│         ▼                ▼                 ▼         │
│  ┌──────────────────────────────────────────────┐   │
│  │              SQLite + Embeddings              │   │
│  │           (local vector search)               │   │
│  └──────────────────────────────────────────────┘   │
│         │                                            │
│         ▼                                            │
│  ┌──────────────────────────────────────────────┐   │
│  │         Docker Volume (~/.brain/data)          │   │
│  │     SQLite DB + markdown exports + config     │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## MCP Tools

brAIn exposes these tools to your AI assistant:

| Tool | Description |
|------|-------------|
| `brain_remember` | Store a piece of knowledge with category and tags |
| `brain_recall` | Semantic search across all memories |
| `brain_forget` | Delete a specific memory |
| `brain_profile` | Get/set user profile and preferences |
| `brain_context` | Get all known context for a project |
| `brain_list` | List memories by category or tag |
| `brain_summarize` | Summarize and store highlights from current conversation |

## Memory Categories

- **identity** — Who you are, your role, your team
- **preferences** — How you like to work, coding style, tools
- **projects** — Repos, architectures, deployment patterns
- **people** — Team members, their roles, expertise areas
- **workflows** — Common commands, processes, runbooks
- **knowledge** — Technical facts, decisions, learnings
- **conversations** — Distilled summaries of past AI conversations

## Quick Start

```bash
# Clone
git clone git@github.com:macsmax/brAIn.git
cd brAIn

# Build and run (use "finch" instead of "docker" if using Finch)
docker compose up -d

# Add to your MCP client config (e.g. ~/.kiro/mcp.json)
# See docs/setup.md for details
```

## Usage

Once brAIn is running and configured in your MCP client, your AI assistant gets access to the brain tools automatically. Just talk naturally — the AI decides when to use them.

### Teaching your brain

Tell the AI things you want it to remember:

```
You:   "Remember that I'm Max, I work on the EC2 Instance Features team, and I prefer concise answers."
AI:    → calls brain_remember(category="identity", content="Max, works on EC2 Instance Features team")
       → calls brain_remember(category="preferences", content="Prefers concise answers")
       "Got it, I'll remember that."

You:   "graf@ is our SEV-SNP expert and diapop@ works on XoN live migration."
AI:    → calls brain_remember(category="people", content="graf@ is the SEV-SNP expert", tags="team,sev-snp")
       → calls brain_remember(category="people", content="diapop@ works on XoN live migration", tags="team,xon")
       "Noted."

You:   "For the mtshare project, the API is FastAPI+PostgreSQL at api.mtshare.net, web is Next.js at mtshare.net."
AI:    → calls brain_remember(category="projects", content="mtshare: FastAPI+PostgreSQL API at api.mtshare.net, Next.js web at mtshare.net", tags="mtshare")
       "Saved."
```

### Recalling knowledge

In a **new conversation** (no prior context), ask naturally:

```
You:   "What do you know about me?"
AI:    → calls brain_recall(query="user identity preferences")
       → calls brain_profile()
       "You're Max, on the EC2 Instance Features team. You prefer concise answers."

You:   "Who on my team knows about SEV-SNP?"
AI:    → calls brain_recall(query="SEV-SNP", category="people")
       "graf@ is your SEV-SNP expert."

You:   "Give me context on the mtshare project."
AI:    → calls brain_context(project="mtshare")
       "mtshare is a universal music link sharing platform — FastAPI+PostgreSQL API at api.mtshare.net, Next.js web at mtshare.net."
```

### Managing memories

```
You:   "List everything you know about people on my team."
AI:    → calls brain_list(category="people")
       Shows all stored people memories.

You:   "Forget memory abc123."
AI:    → calls brain_forget(id="abc123")
       "Done, forgotten."
```

### Profile shortcuts

Profile is a key-value store for quick identity lookups:

```
You:   "Set my profile: name is Max, team is EC2 Instance Features, editor is vim."
AI:    → calls brain_profile(key="name", value="Max")
       → calls brain_profile(key="team", value="EC2 Instance Features")
       → calls brain_profile(key="editor", value="vim")
```

### Browsing your brain

Your brain data is always accessible as files:

```bash
# SQLite database
ls ~/.brain/data/brain.db

# Query directly
sqlite3 ~/.brain/data/brain.db "SELECT id, category, content FROM memories ORDER BY created_at DESC LIMIT 10;"
```

## Configuration

brAIn stores data in `~/.brain/data` on your host machine (mounted as a Docker volume). The database, embeddings, and markdown exports all live there.

```yaml
# docker-compose.yml mounts
volumes:
  - ~/.brain/data:/app/data
```

## Steering File (Recommended)

brAIn ships with a steering file in `steering/brain-first.md` that tells AI assistants to check the brain before answering questions. This ensures your stored knowledge (acronyms, project details, team info, etc.) is used instead of generic responses.

To use it, copy or symlink it into your AI client's steering directory:

```bash
# For Kiro CLI
cp steering/brain-first.md ~/.kiro/steering/brain-first.md

# Or symlink it
ln -s "$(pwd)/steering/brain-first.md" ~/.kiro/steering/brain-first.md
```

Without this, the AI assistant has the brain tools available but won't proactively check them before answering. With it, questions like "what is EPS?" will hit your brain first and return your stored definition instead of a generic one.

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full design.

## Privacy

- All data stored locally in `~/.brain/data`
- Embeddings computed locally using `sentence-transformers` (no external API calls)
- Docker container has no network access after image pull
- You can browse your brain's knowledge as plain markdown files in `~/.brain/data/exports/`

## Roadmap

- [x] Project documentation and architecture
- [x] Core MCP server with remember/recall/forget
- [x] SQLite storage with FTS5 full-text search
- [ ] Local vector embeddings for semantic recall
- [x] Docker/Finch image and compose setup
- [x] Profile and preferences management
- [x] Project context aggregation
- [ ] Conversation summarization
- [ ] Markdown export of brain contents
- [ ] Auto-learning mode (suggest what to remember)
- [ ] Web UI for browsing/editing memories

## License

MIT
