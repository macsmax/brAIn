# Architecture

## Overview

brAIn is a Python MCP server running in Docker that provides persistent memory for AI assistants. It uses SQLite for storage, sentence-transformers for local embeddings, and exposes tools via the MCP protocol.

## Components

### 1. MCP Server (`src/server.py`)

The entry point. Implements the MCP protocol using the `mcp` Python SDK. Registers tools and handles requests from AI clients over stdio transport.

### 2. Memory Store (`src/store.py`)

SQLite-backed storage with two search modes:
- **FTS5** — Full-text keyword search (fast, exact)
- **Vector** — Semantic similarity search using cosine distance on embeddings

Schema:
```sql
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT,           -- comma-separated
    embedding BLOB,      -- float32 vector
    created_at TEXT,
    updated_at TEXT,
    source TEXT           -- 'manual', 'conversation', 'auto'
);

CREATE VIRTUAL TABLE memories_fts USING fts5(content, tags, category);

CREATE TABLE profile (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT
);
```

### 3. Embeddings (`src/embeddings.py`)

Wraps `sentence-transformers/all-MiniLM-L6-v2` (80MB model, runs on CPU). Generates 384-dimensional vectors for semantic search. The model is downloaded once and cached in the Docker volume.

### 4. Exporter (`src/export.py`)

Periodically (or on-demand) exports the brain contents as markdown files to `data/exports/` so you can browse your knowledge base as plain files.

## Data Flow

```
AI says: "Remember that graf@ is the SEV-SNP expert"
    │
    ▼
brain_remember(category="people", content="graf@ is the SEV-SNP expert", tags=["team","sev-snp"])
    │
    ├─► Generate embedding via sentence-transformers
    ├─► Insert into SQLite (memories table + FTS index)
    └─► Return confirmation

AI says: "Who knows about SEV-SNP?"
    │
    ▼
brain_recall(query="SEV-SNP expert")
    │
    ├─► Generate query embedding
    ├─► Cosine similarity search across all memory embeddings
    ├─► Also run FTS5 search for keyword matches
    ├─► Merge and rank results
    └─► Return: "graf@ is the SEV-SNP expert" (similarity: 0.94)
```

## Docker Setup

```
brAIn/
├── Dockerfile
├── docker-compose.yml
├── src/
│   ├── server.py          # MCP server entry point
│   ├── store.py           # SQLite memory store
│   ├── embeddings.py      # Local embedding model
│   ├── export.py          # Markdown exporter
│   └── tools.py           # MCP tool definitions
├── docs/
│   ├── architecture.md    # This file
│   └── setup.md           # Setup guide
├── data/                  # Mounted from ~/.brain/data
│   ├── brain.db           # SQLite database
│   ├── models/            # Cached sentence-transformers model
│   └── exports/           # Markdown exports
└── README.md
```

## MCP Client Configuration

### Kiro CLI (`~/.kiro/settings/mcp.json`)
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

### Alternative: stdio via docker run
```json
{
  "mcpServers": {
    "brain": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "~/.brain/data:/app/data",
        "brain:latest"
      ]
    }
  }
}
```

## Design Principles

1. **Local-first** — No network calls after initial setup. Embeddings run on CPU locally.
2. **Explicit over magic** — The AI or user decides what to remember. No silent data collection.
3. **Browsable** — Markdown exports mean you can always see what the brain knows without any tools.
4. **Portable** — `~/.brain/data` is a single directory. Copy it to a new machine and you're done.
5. **Composable** — Each tool does one thing. The AI orchestrates them based on conversation context.
