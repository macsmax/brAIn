"""brAIn MCP server — local AI second brain."""

import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .store import MemoryStore

app = Server("brain")
store = MemoryStore()

TOOLS = [
    Tool(
        name="brain_remember",
        description="Store a piece of knowledge in the brain. Use this to save facts, preferences, people, workflows, or anything worth remembering across conversations.",
        inputSchema={
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Category: identity, preferences, projects, people, workflows, knowledge, or conversations",
                    "enum": ["identity", "preferences", "projects", "people", "workflows", "knowledge", "conversations"],
                },
                "content": {"type": "string", "description": "The knowledge to remember"},
                "tags": {"type": "string", "description": "Comma-separated tags for filtering (optional)", "default": ""},
            },
            "required": ["category", "content"],
        },
    ),
    Tool(
        name="brain_recall",
        description="Search the brain for relevant memories using semantic similarity. Use this to find previously stored knowledge.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to search for"},
                "category": {"type": "string", "description": "Filter by category (optional)"},
                "limit": {"type": "integer", "description": "Max results (default 5)", "default": 5},
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="brain_forget",
        description="Delete a specific memory by its ID.",
        inputSchema={
            "type": "object",
            "properties": {"id": {"type": "string", "description": "Memory ID to delete"}},
            "required": ["id"],
        },
    ),
    Tool(
        name="brain_list",
        description="List memories, optionally filtered by category or tag.",
        inputSchema={
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Filter by category (optional)"},
                "tag": {"type": "string", "description": "Filter by tag (optional)"},
                "limit": {"type": "integer", "description": "Max results (default 20)", "default": 20},
            },
        },
    ),
    Tool(
        name="brain_profile",
        description="Get or set user profile information. Call with key+value to set, with just key to get one, or with neither to get all.",
        inputSchema={
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Profile key (e.g. 'name', 'team', 'role')"},
                "value": {"type": "string", "description": "Value to set (omit to read)"},
            },
        },
    ),
    Tool(
        name="brain_context",
        description="Get all known context about a project — combines project memories with related knowledge.",
        inputSchema={
            "type": "object",
            "properties": {"project": {"type": "string", "description": "Project name to get context for"}},
            "required": ["project"],
        },
    ),
]


@app.list_tools()
async def list_tools():
    return TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "brain_remember":
        result = store.remember(arguments["category"], arguments["content"], arguments.get("tags", ""))
    elif name == "brain_recall":
        result = store.recall(arguments["query"], arguments.get("category"), arguments.get("limit", 5))
    elif name == "brain_forget":
        result = store.forget(arguments["id"])
    elif name == "brain_list":
        result = store.list_memories(arguments.get("category"), arguments.get("tag"), arguments.get("limit", 20))
    elif name == "brain_profile":
        if "value" in arguments and arguments["value"]:
            result = store.set_profile(arguments["key"], arguments["value"])
        else:
            result = store.get_profile(arguments.get("key"))
    elif name == "brain_context":
        result = store.context(arguments["project"])
    else:
        result = {"error": f"Unknown tool: {name}"}

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
