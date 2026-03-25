# Setup Guide

## Prerequisites

- Docker and Docker Compose
- An MCP-compatible AI client (Kiro CLI, Claude Desktop, etc.)

## Installation

### 1. Clone the repo

```bash
git clone git@github.com:macsmax/brAIn.git
cd brAIn
```

### 2. Create the data directory

```bash
mkdir -p ~/.brain/data
```

### 3. Build and start

```bash
docker compose up -d
```

The first run will download the sentence-transformers model (~80MB). This is cached in `~/.brain/data/models/` for subsequent runs.

### 4. Configure your MCP client

Add brAIn to your MCP client configuration.

**Kiro CLI** — edit `~/.kiro/settings/mcp.json`:
```json
{
  "mcpServers": {
    "brain": {
      "command": "docker",
      "args": ["exec", "-i", "brain", "python", "-m", "src.server"],
      "disabled": false
    }
  }
}
```

**Claude Desktop** — edit `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "brain": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "${HOME}/.brain/data:/app/data",
        "brain:latest"
      ]
    }
  }
}
```

### 5. Verify

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

All data lives in `~/.brain/data/`:

```
~/.brain/data/
├── brain.db        # SQLite database (memories, profile, embeddings)
├── models/         # Cached sentence-transformers model
└── exports/        # Markdown exports of your brain contents
    ├── people.md
    ├── projects.md
    ├── workflows.md
    └── ...
```

## Backup

Just copy `~/.brain/data/` — it's a self-contained directory with everything.

```bash
cp -r ~/.brain/data ~/.brain/backup-$(date +%Y%m%d)
```

## Updating

```bash
cd brAIn
git pull
docker compose build
docker compose up -d
```
