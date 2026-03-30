"""brAIn MCP server — local AI second brain."""

import json
from typing import Optional
from mcp.server.fastmcp import FastMCP

from .store import MemoryStore

mcp = FastMCP("brain", stateless_http=True)
store = MemoryStore()

CATEGORIES = ["identity", "preferences", "projects", "people", "workflows", "knowledge", "conversations"]


@mcp.tool()
def brain_remember(category: str, content: str, tags: str = "") -> str:
    """Store a piece of knowledge in the brain. Use this to save facts, preferences, people, workflows, or anything worth remembering across conversations.

    Args:
        category: Category: identity, preferences, projects, people, workflows, knowledge, or conversations
        content: The knowledge to remember
        tags: Comma-separated tags for filtering (optional)
    """
    return json.dumps(store.remember(category, content, tags), indent=2)


@mcp.tool()
def brain_recall(query: str, category: Optional[str] = None, limit: int = 5) -> str:
    """Search the brain for relevant memories using semantic similarity. Use this to find previously stored knowledge.

    Args:
        query: What to search for
        category: Filter by category (optional)
        limit: Max results (default 5)
    """
    return json.dumps(store.recall(query, category, limit), indent=2)


@mcp.tool()
def brain_forget(id: str) -> str:
    """Delete a specific memory by its ID.

    Args:
        id: Memory ID to delete
    """
    return json.dumps(store.forget(id), indent=2)


@mcp.tool()
def brain_list(category: Optional[str] = None, tag: Optional[str] = None, limit: int = 20) -> str:
    """List memories, optionally filtered by category or tag.

    Args:
        category: Filter by category (optional)
        tag: Filter by tag (optional)
        limit: Max results (default 20)
    """
    return json.dumps(store.list_memories(category, tag, limit), indent=2)


@mcp.tool()
def brain_profile(key: Optional[str] = None, value: Optional[str] = None) -> str:
    """Get or set user profile information. Call with key+value to set, with just key to get one, or with neither to get all.

    Args:
        key: Profile key (e.g. 'name', 'team', 'role')
        value: Value to set (omit to read)
    """
    if value:
        return json.dumps(store.set_profile(key, value), indent=2)
    return json.dumps(store.get_profile(key), indent=2)


@mcp.tool()
def brain_context(project: str) -> str:
    """Get all known context about a project — combines project memories with related knowledge.

    Args:
        project: Project name to get context for
    """
    return json.dumps(store.context(project), indent=2)


@mcp.tool()
def brain_summarize(summary: str, tags: str = "") -> str:
    """Summarize and store highlights from current conversation.

    Args:
        summary: Distilled summary of the conversation
        tags: Comma-separated tags for filtering (optional)
    """
    return json.dumps(store.summarize(summary, tags), indent=2)


@mcp.tool()
def brain_export() -> str:
    """Export all brain contents as markdown. Also saves to data/exports/brain.md."""
    return store.export_markdown()


@mcp.tool()
def brain_suggest(text: str) -> str:
    """Suggest what to remember from a block of text. Returns novel information not already in the brain.

    Args:
        text: Text to analyze for potential memories
    """
    return json.dumps(store.suggest(text), indent=2)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp.streamable_http_app(), host="0.0.0.0", port=8765)
