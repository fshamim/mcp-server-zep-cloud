# MCP Server for Zep Cloud

Give Claude and Codex long-term memory via [Zep Cloud](https://www.getzep.com/) — store conversations, search a knowledge graph, and recall context across sessions.

## Prerequisites

Get a free Zep Cloud API key at [app.getzep.com](https://app.getzep.com/).

## Quick Start

### Claude Code (CLI)

```bash
claude mcp add zep-cloud \
  -e ZEP_API_KEY=your-key \
  -- uvx --from git+https://github.com/fshamim/mcp-server-zep-cloud mcp-server-zep-cloud
```

### Codex CLI

```bash
codex mcp add zep-cloud \
  -e ZEP_API_KEY=your-key \
  -- uvx --from git+https://github.com/fshamim/mcp-server-zep-cloud mcp-server-zep-cloud
```

### Claude Desktop / Codex Desktop

Add to your config file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

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
        "ZEP_API_KEY": "your-key"
      }
    }
  }
}
```

### Setup Script (clone + install)

```bash
git clone https://github.com/fshamim/mcp-server-zep-cloud.git
cd mcp-server-zep-cloud
python scripts/install.py
```

The script installs the package, prompts for your API key, and configures Claude Desktop automatically.

## Concepts

Understanding Zep's data model helps you use the tools correctly.

- **User** (`user_id`): The identity whose memory is being stored — a person, an AI agent, or any entity. Each user has their own isolated knowledge graph. Defaults to `"default_user"` when omitted.
- **Thread** (`session_id`): A conversation or work session *within* a user's memory. Multiple threads per user are normal; Zep links facts across them automatically via the knowledge graph.
- **Graph**: Entities and relationships auto-extracted from all of a user's threads. Searchable via `zep_search_memory`, browsable via `zep_get_graph_nodes` / `zep_get_graph_edges`.

## Claude Code Integration

### Set the active user at session start

Run the `/zep-context` skill at the beginning of a session to declare which Zep user all memory calls should target:

```
/zep-context fshamim
```

For the rest of the session, every Zep tool call will automatically receive `user_id: "fshamim"`.

### Auto-memory → Zep sync (hook)

Claude Code's auto-memory feature writes notes to `memory/*.md` files. The included hook syncs those writes to Zep automatically so they persist in the knowledge graph.

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
