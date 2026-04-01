# brAIn 🧠

A local, private MCP (Model Context Protocol) server that acts as your AI second brain. It persists knowledge across conversations — who you are, how you work, your projects, your team, your workflows — so every AI conversation starts with context instead of from scratch.

## Why

Every time you start a new AI chat, you lose context. You re-explain your setup, your team, your preferences. brAIn fixes this by running a local MCP server in Docker (or Finch) that remembers everything you tell it and lets any MCP-compatible AI assistant (Kiro, Claude, etc.) recall that knowledge.

**Everything stays on your machine. No cloud. No API keys for storage. Fully private.**

> Works with [Docker](https://www.docker.com/) or [Finch](https://runfinch.com/) (just replace `docker` with `finch` in the commands below).

## How It Works

```
┌──────────────────────────────────────────────────────┐
│                     AI Assistant                     │
│                 (Kiro, Claude, etc.)                 │
└───────────────────────────┬──────────────────────────┘
                            │ MCP Protocol (stdio/SSE)
                            ▼
┌──────────────────────────────────────────────────────┐
│                   brAIn MCP Server                   │
│               (Docker/Finch container)               │
│                                                      │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│ │    Memory    │  │   Semantic   │  │   Profile    │ │
│ │   Manager    │  │    Search    │  │   Manager    │ │
│ └───────┬──────┘  └───────┬──────┘  └───────┬──────┘ │
│         │                 │                 │        │
│         ▼                 ▼                 ▼        │
│  ┌────────────────────────────────────────────────┐  │
│  │              SQLite + Embeddings               │  │
│  │             (local vector search)              │  │
│  └────────────────────────────────────────────────┘  │
│         │                                            │
│         ▼                                            │
│  ┌────────────────────────────────────────────────┐  │
│  │         Docker Volume (~/.brain/data)          │  │
│  │     SQLite DB + markdown exports + config      │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
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
| `brain_export` | Export all brain contents as markdown |
| `brain_suggest` | Suggest what to remember from a block of text |

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
```

Then configure your MCP client. For Kiro CLI:

```bash
# 1. MCP server config
mkdir -p ~/.kiro/settings
cat > ~/.kiro/settings/mcp.json << 'EOF'
{
  "mcpServers": {
    "brain": {
      "url": "http://localhost:8765/mcp",
      "disabled": false
    }
  }
}
EOF

# 2. Agent config (auto-approves brAIn tools)
mkdir -p ~/.kiro/agents
cat > ~/.kiro/agents/default.json << 'EOF'
{
  "name": "default",
  "tools": ["*"],
  "allowedTools": ["fs_read", "@brain"],
  "resources": ["file://README.md", "file://.kiro/rules/**/*.md"],
  "useLegacyMcpJson": true
}
EOF
kiro-cli settings chat.defaultAgent default

# 3. Steering file (recommended — makes AI check brain proactively)
mkdir -p ~/.kiro/steering
cp steering/brain-first.md ~/.kiro/steering/brain-first.md
```

See [docs/setup.md](docs/setup.md) for full details including Claude Desktop config.

## Usage

Once brAIn is running and configured in your MCP client, your AI assistant gets access to the brain tools automatically. Just talk naturally — the AI decides when to use them.

### Teaching your brain

Tell the AI things you want it to remember:

```
You:   "Remember that I'm Max, I work on the EC2 Instance Features team, and I prefer concise answers."
AI:    → calls brain_remember(category="identity", content="Max, works on EC2 Instance Features team")
       → calls brain_remember(category="preferences", content="Prefers concise answers")
       "Got it, I'll remember that."

You:   "user1@ is our project2 expert and user2@ works on project1."
AI:    → calls brain_remember(category="people", content="user1@ is the project2 expert", tags="team,project2")
       → calls brain_remember(category="people", content="user2@ works on project1", tags="team,project1")
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

You:   "Who on my team knows about project2?"
AI:    → calls brain_recall(query="project2", category="people")
       "user1@ is your project2 expert."

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

## Auto-Approving Tools (Kiro CLI)

By default, Kiro CLI asks for confirmation before running MCP tools. To auto-approve all brAIn tools, add `"@brain"` to the `allowedTools` list in your agent configuration:

```json
// ~/.kiro/agents/default.json
{
  "name": "default",
  "tools": ["*"],
  "allowedTools": [
    "fs_read",
    "@brain"
  ],
  "resources": ["file://README.md", "file://KIRO.md", "file://.kiro/rules/**/*.md"],
  "useLegacyMcpJson": true
}
```

Then set it as your default agent:

```bash
kiro-cli settings chat.defaultAgent default
```

The `"@brain"` wildcard auto-approves all tools from the `brain` MCP server (`brain_remember`, `brain_recall`, `brain_forget`, `brain_profile`, `brain_context`, `brain_list`).

Alternatively, for session-only trust, start with:

```bash
kiro-cli chat --trust-tools=@brain/brain_recall,@brain/brain_remember,@brain/brain_forget,@brain/brain_profile,@brain/brain_context,@brain/brain_list
```

## Web UI

brAIn includes a web interface for browsing and editing memories at `http://localhost:8766`. It runs alongside the MCP server in the same container.

Features:
- Browse and search memories with semantic search
- Filter by category
- Add new memories
- Delete memories
- View and set profile
- Export brain contents as markdown

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full design.

## Networking and Security

By default, both the MCP server (port 8765) and web UI (port 8766) are bound to `127.0.0.1` (localhost only). This means only processes on your machine can reach them.

```yaml
# Default: localhost only (recommended for single-user)
ports:
  - "127.0.0.1:8765:8765"
  - "127.0.0.1:8766:8766"
```

If you want multiple AI agents on different machines to share the same brain, remove the `127.0.0.1` prefix to bind on all interfaces:

```yaml
# Network-accessible (for multi-agent setups)
ports:
  - "8765:8765"
  - "8766:8766"
```

Remote agents can then connect using HTTP transport by pointing their MCP client config to `http://<your-ip>:8765/mcp`. Note that stdio transport won't work remotely; the agent must support HTTP-based MCP (streamable HTTP or SSE).

**Warning:** There is no authentication. Anyone who can reach the port can read, write, and delete your memories. Only expose to the network if you trust it (e.g. a private LAN or VPN). For untrusted networks, consider putting a reverse proxy with auth in front.

## Privacy

- All data stored locally in `~/.brain/data`
- Embeddings computed locally using `sentence-transformers` (no external API calls)
- Docker container has no network access after image pull
- Ports bound to localhost by default; not reachable from the network
- You can browse your brain's knowledge as plain markdown files in `~/.brain/data/exports/`

## Roadmap

- [x] Project documentation and architecture
- [x] Core MCP server with remember/recall/forget
- [x] SQLite storage with FTS5 full-text search
- [x] Local vector embeddings for semantic recall
- [x] Docker/Finch image and compose setup
- [x] Profile and preferences management
- [x] Project context aggregation
- [x] Conversation summarization
- [x] Markdown export of brain contents
- [x] Auto-learning mode (suggest what to remember)
- [x] Web UI for browsing/editing memories

## License

MIT
