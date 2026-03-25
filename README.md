# brAIn 🧠

A local, private MCP (Model Context Protocol) server that acts as your AI second brain. It persists knowledge across conversations — who you are, how you work, your projects, your team, your workflows — so every AI conversation starts with context instead of from scratch.

## Why

Every time you start a new AI chat, you lose context. You re-explain your setup, your team, your preferences. brAIn fixes this by running a local MCP server in Docker that remembers everything you tell it and lets any MCP-compatible AI assistant (Kiro, Claude, etc.) recall that knowledge.

**Everything stays on your machine. No cloud. No API keys for storage. Fully private.**

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
│                (Docker container)                     │
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

# Build and run
docker compose up -d

# Add to your MCP client config (e.g. ~/.kiro/mcp.json)
# See docs/setup.md for details
```

## Configuration

brAIn stores data in `~/.brain/data` on your host machine (mounted as a Docker volume). The database, embeddings, and markdown exports all live there.

```yaml
# docker-compose.yml mounts
volumes:
  - ~/.brain/data:/app/data
```

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full design.

## Privacy

- All data stored locally in `~/.brain/data`
- Embeddings computed locally using `sentence-transformers` (no external API calls)
- Docker container has no network access after image pull
- You can browse your brain's knowledge as plain markdown files in `~/.brain/data/exports/`

## Roadmap

- [x] Project documentation and architecture
- [ ] Core MCP server with remember/recall/forget
- [ ] SQLite storage with FTS5 full-text search
- [ ] Local vector embeddings for semantic recall
- [ ] Docker image and compose setup
- [ ] Profile and preferences management
- [ ] Project context aggregation
- [ ] Conversation summarization
- [ ] Markdown export of brain contents
- [ ] Auto-learning mode (suggest what to remember)
- [ ] Web UI for browsing/editing memories

## License

MIT
