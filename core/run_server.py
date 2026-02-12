#!/usr/bin/env python3
"""
Entry point for the Zep Cloud MCP Server.
Runs the server using stdio transport.
"""

import asyncio

try:
    from core.zep_cloud_server import main
except ImportError:
    from zep_cloud_server import main


def main_sync():
    """Synchronous entry point for console_scripts."""
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
