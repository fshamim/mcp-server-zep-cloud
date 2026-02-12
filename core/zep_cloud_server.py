#!/usr/bin/env python3
"""
MCP Server for Zep Cloud (v3)
Provides 7 tools for thread-based memory management and knowledge graph exploration.
Uses stdio transport for CLI compatibility (Claude Desktop, Codex CLI, etc.).
"""

import sys
import json
import logging

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

try:
    from core.zep_cloud_client import ZepCloudClient
except ImportError:
    from zep_cloud_client import ZepCloudClient

load_dotenv()

# All logging must go to stderr — stdout is reserved for MCP protocol
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("ZepCloudServer")

# Initialize client
try:
    client = ZepCloudClient()
    logger.info("Zep Cloud client ready")
except Exception as e:
    logger.error(f"Failed to initialize Zep Cloud client: {e}")
    client = None

# Create MCP server
server = Server("zep-cloud")

# --- Tool Definitions ---

TOOLS = [
    Tool(
        name="zep_store_memory",
        description=(
            "Store content in a Zep memory thread. Creates the thread automatically if it "
            "doesn't exist. Use this to save conversation context, facts, or any information "
            "that should be remembered across sessions."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Thread/session identifier. Use a consistent ID to group related memories.",
                },
                "content": {
                    "type": "string",
                    "description": "The content to store in memory.",
                },
                "role": {
                    "type": "string",
                    "description": "Message role: 'user', 'assistant', or 'system'.",
                    "default": "assistant",
                },
            },
            "required": ["session_id", "content"],
        },
    ),
    Tool(
        name="zep_search_memory",
        description=(
            "Semantic search across the user's knowledge graph. Returns matching facts "
            "(edges) and entities (nodes) ranked by relevance. Use this to recall information "
            "about the user or previously stored context."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return.",
                    "default": 10,
                },
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="zep_get_memory",
        description=(
            "Retrieve messages from a memory thread. Supports pagination and filtering "
            "by role. Use lastn for the N most recent messages, or limit+cursor for pagination."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Thread/session identifier to retrieve messages from.",
                },
                "lastn": {
                    "type": "integer",
                    "description": "Return the N most recent messages (overrides limit/cursor).",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of messages to return (use with cursor for pagination).",
                },
                "cursor": {
                    "type": "integer",
                    "description": "Pagination cursor (use with limit).",
                },
                "role_filter": {
                    "type": "string",
                    "description": "Filter messages by role: 'user', 'assistant', or 'system'.",
                },
            },
            "required": ["session_id"],
        },
    ),
    Tool(
        name="zep_get_graph_nodes",
        description=(
            "List all entities (nodes) in the user's knowledge graph. Each node represents "
            "a person, place, concept, or other entity extracted from conversations."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of nodes to return.",
                    "default": 50,
                },
            },
        },
    ),
    Tool(
        name="zep_get_graph_edges",
        description=(
            "List all relationships (edges/facts) in the user's knowledge graph. Each edge "
            "represents a fact connecting two entities, e.g. 'Alice WORKS_AT Acme Corp'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of edges to return.",
                    "default": 50,
                },
            },
        },
    ),
    Tool(
        name="zep_get_node_details",
        description=(
            "Get detailed information about a specific entity node, including all its "
            "relationships (edges) and the episodes (conversation excerpts) where it was mentioned."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "node_uuid": {
                    "type": "string",
                    "description": "UUID of the node to get details for.",
                },
            },
            "required": ["node_uuid"],
        },
    ),
    Tool(
        name="zep_get_thread_context",
        description=(
            "Retrieve relevant context from all past threads for the current session. "
            "This provides cross-thread memory, pulling in relevant information from "
            "previous conversations. Use 'summary' mode for detailed context or 'basic' for faster responses."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Thread/session identifier to get context for.",
                },
                "mode": {
                    "type": "string",
                    "description": "Context mode: 'summary' (detailed) or 'basic' (faster).",
                    "default": "summary",
                },
            },
            "required": ["session_id"],
        },
    ),
]


@server.list_tools()
async def list_tools():
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if client is None:
        return [TextContent(type="text", text=json.dumps({"error": "Zep client not initialized. Check ZEP_API_KEY."}))]

    try:
        if name == "zep_store_memory":
            result = client.store_memory(
                session_id=arguments["session_id"],
                content=arguments["content"],
                role=arguments.get("role", "assistant"),
                metadata=arguments.get("metadata"),
            )

        elif name == "zep_search_memory":
            result = client.search_graph(
                query=arguments["query"],
                limit=arguments.get("limit", 10),
            )

        elif name == "zep_get_memory":
            kwargs = {"session_id": arguments["session_id"]}
            if "lastn" in arguments:
                kwargs["lastn"] = arguments["lastn"]
            if "limit" in arguments:
                kwargs["limit"] = arguments["limit"]
            if "cursor" in arguments:
                kwargs["cursor"] = arguments["cursor"]

            result = client.get_memory(**kwargs)

            # Apply role filter client-side if specified
            role_filter = arguments.get("role_filter")
            if role_filter and "messages" in result:
                result["messages"] = [m for m in result["messages"] if m.get("role") == role_filter]
                result["message_count"] = len(result["messages"])

        elif name == "zep_get_graph_nodes":
            result = client.get_graph_nodes(limit=arguments.get("limit", 50))

        elif name == "zep_get_graph_edges":
            result = client.get_graph_edges(limit=arguments.get("limit", 50))

        elif name == "zep_get_node_details":
            result = client.get_node_details(node_uuid=arguments["node_uuid"])

        elif name == "zep_get_thread_context":
            result = client.get_thread_context(
                session_id=arguments["session_id"],
                mode=arguments.get("mode", "summary"),
            )

        else:
            result = {"error": f"Unknown tool: {name}"}

        return [TextContent(type="text", text=json.dumps(result))]

    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    logger.info("Starting Zep Cloud MCP Server (stdio)")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
