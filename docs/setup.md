# Setup Guide

## Prerequisites

- Docker or [Finch](https://runfinch.com/) (use `finch` instead of `docker` in the commands below)
- An MCP-compatible AI client (Kiro CLI, Claude Desktop, etc.)

## Installation

### 1. Clone the repo

```bash
git clone ssh://git.amazon.com/pkg/BrAIn -b dev
cd BrAIn
```

### 2. Build and start

```bash
docker compose up -d
```

The first run will download the sentence-transformers model (~80MB). This is cached in `data/models/` for subsequent runs.

### 3. Configure your MCP client

brAIn exposes an HTTP endpoint at `http://localhost:8765/mcp/`. Add it to your MCP client configuration. The trailing slash is important — some MCP clients (e.g. Kiro CLI) require it.

#### Kiro CLI

You need to set up three files: the MCP server config, an agent config, and (optionally) a steering file.

**a) MCP server config** — create `~/.kiro/settings/mcp.json`:

```bash
mkdir -p ~/.kiro/settings
cat > ~/.kiro/settings/mcp.json << 'EOF'
{
  "mcpServers": {
    "brain": {
      "url": "http://localhost:8765/mcp/",
      "disabled": false,
      "autoApprove": [
        "brain_remember",
        "brain_recall",
        "brain_forget",
        "brain_list",
        "brain_profile",
        "brain_context"
      ]
    }
  }
}
EOF
```

This tells Kiro CLI where the brAIn MCP server is and which tools to auto-approve.

**b) Agent config** — create `~/.kiro/agents/default.json`:

```bash
mkdir -p ~/.kiro/agents
cat > ~/.kiro/agents/default.json << 'EOF'
{
  "name": "default",
  "description": "Default agent with brAIn MCP tools auto-approved",
  "tools": ["*"],
  "allowedTools": [
    "fs_read",
    "@brain"
  ],
  "resources": ["file://README.md", "file://KIRO.md", "file://.kiro/rules/**/*.md"],
  "useLegacyMcpJson": true
}
EOF
```

The `"@brain"` entry auto-approves all tools from the `brain` MCP server without confirmation prompts. The `useLegacyMcpJson` flag tells Kiro to read from `~/.kiro/settings/mcp.json`.

Then set it as your default agent:

```bash
kiro-cli settings chat.defaultAgent default
```

**c) Steering file (recommended)** — tells the AI to check brAIn before answering:

```bash
mkdir -p ~/.kiro/steering
cp steering/brain-first.md ~/.kiro/steering/brain-first.md
```

Without this, the AI has the brain tools but won't proactively check them. With it, questions like "what is EPS?" will hit your brain first.

#### Claude Code

Claude Code requires `"type": "http"` for HTTP-based MCP servers. You can also add it via CLI: `claude mcp add --transport http --scope user brain http://localhost:8765/mcp`. Add the following to `~/.claude/settings.json` (global) or `.claude/settings.json` (project-level):

```json
{
  "mcpServers": {
    "brain": {
      "type": "http",
      "url": "http://localhost:8765/mcp"
    }
  },
  "permissions": {
    "allow": [
      "mcp__brain__brain_remember",
      "mcp__brain__brain_recall",
      "mcp__brain__brain_forget",
      "mcp__brain__brain_list",
      "mcp__brain__brain_profile",
      "mcp__brain__brain_context"
    ]
  }
}
```

The `permissions.allow` list auto-approves these tools so Claude Code won't prompt for confirmation each time. The pattern is `mcp__<server-name>__<tool-name>`.

For the steering file:

```bash
cp steering/brain-first.md ~/.claude/rules/brain-mcp.md
```

This creates a global rule that tells Claude Code to check brAIn before answering knowledge questions.

#### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "brain": {
      "url": "http://localhost:8765/mcp/"
    }
  }
}
```

### 4. Verify

Start a conversation with your AI assistant and ask it to:
```
Remember that my name is <your name> and I work on <your team>
```

Then in a new conversation:
```
What do you know about me?
```

If brAIn is working, the AI will recall your name and team from the previous conversation.

## Data Location

All data lives in the `data/` directory relative to the repo:

```
data/
├── brain.db        # SQLite database (memories, profile, embeddings)
├── models/         # Cached sentence-transformers model
└── exports/        # Markdown exports of your brain contents
    ├── people.md
    ├── projects.md
    ├── workflows.md
    └── ...
```

## Backup

Just copy the `data/` directory.

```bash
cp -r data data-backup-$(date +%Y%m%d)
```

## Troubleshooting

### AL2 Cloud Desktop: docker-buildx errors

The version of `docker-buildx` bundled with AL2 may be too old for the compose build. Update it manually:

```bash
sudo mv /usr/libexec/docker/cli-plugins/docker-buildx /usr/libexec/docker/cli-plugins/docker-buildx_bak
sudo curl -L https://github.com/docker/buildx/releases/download/v0.33.0/buildx-v0.33.0.linux-amd64 \
  -o /usr/libexec/docker/cli-plugins/docker-buildx
sudo chmod 755 /usr/libexec/docker/cli-plugins/docker-buildx
```

### Kiro CLI: "JSON parse error" or "default not found"

If you see errors like:
```
Json supplied at ~/.kiro/agents/default.json is invalid
WARNING: Failed to parse MCP config ~/.kiro/settings/mcp.json: JSON parse error
Error: user defined default default not found
```

The config files are empty or malformed. Recreate them using the `cat` commands in the [Quick Start](#quick-start) section or [docs/setup.md](docs/setup.md).

## Updating

```bash
git pull
docker compose build
docker compose up -d
```
