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

## Available Tools

| Tool | Description |
|------|-------------|
| `zep_store_memory` | Store content in a memory thread (auto-creates thread) |
| `zep_get_memory` | Retrieve messages from a thread with pagination and role filtering |
| `zep_search_memory` | Semantic search across the user's knowledge graph |
| `zep_get_graph_nodes` | List all entities (nodes) in the knowledge graph |
| `zep_get_graph_edges` | List all relationships (edges/facts) in the knowledge graph |
| `zep_get_node_details` | Get detailed info about a node including edges and episodes |
| `zep_get_thread_context` | Cross-thread context retrieval from past conversations |

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
