# MCP Server for Zep Cloud

Give Claude and Codex long-term memory via [Zep Cloud](https://www.getzep.com/) — store conversations, search a knowledge graph, and recall context across sessions.

## Prerequisites

Get a free Zep Cloud API key at [app.getzep.com](https://app.getzep.com/).

## Quick Start

### Claude Code (CLI)

```bash
claude mcp add zep-cloud \
  -e ZEP_API_KEY=your-key \
  -e ZEP_DEFAULT_USER_ID=your-user-id \
  -- uvx --from git+https://github.com/fshamim/mcp-server-zep-cloud mcp-server-zep-cloud
```

### Codex CLI

```bash
codex mcp add zep-cloud \
  -e ZEP_API_KEY=your-key \
  -e ZEP_DEFAULT_USER_ID=your-user-id \
  -- uvx --from git+https://github.com/fshamim/mcp-server-zep-cloud mcp-server-zep-cloud
```

### Claude Desktop / Codex Desktop

Add to your config file:

- **macOS Claude Desktop**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows Claude Desktop**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS Codex Desktop**: `~/Library/Application Support/Codex/codex_desktop_config.json`

```json
{
  "mcpServers": {
    "zep-cloud": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/fshamim/mcp-server-zep-cloud",
        "mcp-server-zep-cloud"
      ],
      "env": {
        "ZEP_API_KEY": "your-key",
        "ZEP_DEFAULT_USER_ID": "your-user-id"
      }
    }
  }
}
```

`ZEP_DEFAULT_USER_ID` sets the user for all tool calls that don't explicitly pass a `user_id`. Omit it to fall back to `"default_user"`. Desktop apps don't have a skill system, so this env var is the recommended way to set your identity.

### Setup Script (clone + install)

```bash
git clone https://github.com/fshamim/mcp-server-zep-cloud.git
cd mcp-server-zep-cloud
python scripts/install.py
```

The script installs the package, prompts for your API key, and configures Claude Desktop automatically.

## Concepts

Understanding Zep's data model helps you use the tools correctly.

- **User** (`user_id`): The identity whose memory is being stored — a person, an AI agent, or any entity. Each user has their own isolated knowledge graph.
- **Thread** (`session_id`): A conversation or work session *within* a user's memory. Multiple threads per user are normal; Zep links facts across them automatically via the knowledge graph.
- **Graph**: Entities and relationships auto-extracted from all of a user's threads. Searchable via `zep_search_memory`, browsable via `zep_get_graph_nodes` / `zep_get_graph_edges`.

## Setting the User Identity

Every tool that touches user data accepts an optional `user_id` argument. There are three ways to set it, applied in this priority order (highest wins):

### 1. Per tool call (any client)

Pass `user_id` directly in the tool call. This overrides everything else for that single call:

```
zep_store_memory(session_id="s1", content="...", user_id="alice")
```

### 2. Per session — Claude Code CLI only

Run the `/zep-context` skill at the start of a session. Claude will pass that `user_id` to every Zep tool call for the rest of the conversation:

```
/zep-context fshamim
```

This overrides `ZEP_DEFAULT_USER_ID` for the session, but individual tool calls can still override it further.

### 3. Server default — all clients

Set `ZEP_DEFAULT_USER_ID` as an environment variable when starting the server. Every tool call that doesn't explicitly pass a `user_id` will use this value. Falls back to `"default_user"` if not set.

**Claude Desktop / Codex Desktop** — set it in your config JSON (this is the only option available in desktop apps since they have no skill system):

```json
"env": {
  "ZEP_API_KEY": "your-key",
  "ZEP_DEFAULT_USER_ID": "fshamim"
}
```

**Claude Code / Codex CLI** — pass it when adding the server:

```bash
-e ZEP_DEFAULT_USER_ID=fshamim
```

Even with `ZEP_DEFAULT_USER_ID` set, you or Claude can still address a different user at any time by passing `user_id` explicitly in a tool call. The desktop apps support this — just ask Claude to use a specific user when storing or retrieving memory.

## Claude Code Integration

### Auto-memory → Zep sync (hook)

Claude Code writes notes to `memory/*.md` files during sessions. The included hook syncs those writes to Zep automatically so they persist in the knowledge graph.

**Setup:**

1. Set environment variables in `.claude/settings.local.json` (gitignored, keeps credentials private):

```json
{
  "env": {
    "ZEP_API_KEY": "your-key-here",
    "ZEP_USER_ID": "your-user-id-here"
  }
}
```

2. Enable the hook by copying the hook config from `.claude/settings.json` into your local settings, or configure it globally in `~/.claude/settings.json`.

3. Ensure `zep-cloud` is importable in your Python environment:

```bash
pip install zep-cloud
# or, if the server is already installed:
pip install -e .
```

**How it works:** After every `Write` or `Edit` tool call that touches a `memory/*.md` file, `hooks/sync_memory_to_zep.py` runs asynchronously. It reads the file content and stores it as a system message in the thread `claude_code_memory_{ZEP_USER_ID}`. The hook exits silently if `ZEP_API_KEY` or `ZEP_USER_ID` is not set, so it never interferes with normal Claude Code operation.

## Available Tools

All tools that operate on user-specific data accept an optional `user_id` parameter (defaults to `"default_user"`).

| Tool | Description |
|------|-------------|
| `zep_store_memory` | Store content in a memory thread (auto-creates user + thread) |
| `zep_get_memory` | Retrieve messages from a thread with pagination and role filtering |
| `zep_search_memory` | Semantic search across a user's knowledge graph |
| `zep_get_graph_nodes` | List all entities (nodes) in a user's knowledge graph |
| `zep_get_graph_edges` | List all relationships (edges/facts) in a user's knowledge graph |
| `zep_get_node_details` | Get detailed info about a node including edges and episodes |
| `zep_get_thread_context` | Cross-thread context retrieval from a user's past conversations |

## Docker

```bash
docker build -t mcp-server-zep-cloud .
docker run -e ZEP_API_KEY="your-key" mcp-server-zep-cloud
```

## Development

### Project Structure

```
core/
  run_server.py          — Entry point, runs asyncio event loop
  zep_cloud_server.py    — MCP server with 7 tools, stdio transport
  zep_cloud_client.py    — API client wrapping zep-cloud SDK v3
config/
  requirements.txt       — Dependencies (for manual/Smithery installs)
  .env.example           — Template for environment variables
scripts/
  install.py             — Automated setup script
tests/
  test_server_tools.py   — Unit tests (no API key needed)
  test_v3_compatibility.py — Integration tests (requires ZEP_API_KEY)
pyproject.toml           — Package metadata and build config
```

### Install for Development

```bash
pip install -e .
```

### Run the Server

```bash
mcp-server-zep-cloud          # via console entry point
python core/run_server.py     # direct execution
```

### Run Tests

```bash
python tests/test_server_tools.py        # Unit tests (no API key needed)
python tests/test_v3_compatibility.py    # Integration tests (requires ZEP_API_KEY)
```

## License

MIT — see [LICENSE](LICENSE).
