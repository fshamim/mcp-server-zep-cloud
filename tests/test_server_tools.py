#!/usr/bin/env python3
"""
Unit tests for MCP server tool definitions and dispatch.
No API key required — uses a mock client.

Run: python tests/test_server_tools.py
"""

import os
import sys
import json
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

PASS = 0
FAIL = 0


def log(status, name, detail=""):
    global PASS, FAIL
    icon = "PASS" if status else "FAIL"
    if status:
        PASS += 1
    else:
        FAIL += 1
    msg = f"[{icon}] {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)


class MockClient:
    """Mock ZepCloudClient for testing tool dispatch without API calls."""

    def store_memory(self, session_id, content, role="assistant", metadata=None):
        return {"success": True, "thread_id": session_id, "role": role, "content_length": len(content)}

    def get_memory(self, session_id, lastn=None, limit=None, cursor=None):
        return {
            "thread_id": session_id,
            "message_count": 2,
            "messages": [
                {"uuid": "msg-1", "role": "user", "content": "Hello", "created_at": None, "metadata": None},
                {"uuid": "msg-2", "role": "assistant", "content": "Hi there", "created_at": None, "metadata": None},
            ],
        }

    def search_graph(self, query, limit=10):
        return {"query": query, "edge_count": 0, "node_count": 0, "edges": [], "nodes": []}

    def get_graph_nodes(self, limit=50):
        return {"node_count": 1, "nodes": [{"uuid": "n-1", "name": "Alice", "labels": ["Person"], "summary": None, "created_at": None}]}

    def get_graph_edges(self, limit=50):
        return {"edge_count": 1, "edges": [{"uuid": "e-1", "fact": "Alice likes blue", "name": "LIKES", "source_node_uuid": "n-1", "target_node_uuid": "n-2", "created_at": None}]}

    def get_node_details(self, node_uuid):
        return {
            "node": {"uuid": node_uuid, "name": "Alice", "labels": ["Person"], "summary": None, "attributes": {}, "created_at": None},
            "edge_count": 0, "edges": [],
            "episode_count": 0, "episodes": [],
        }

    def get_thread_context(self, session_id, mode="summary"):
        return {"thread_id": session_id, "mode": mode, "context": "Some context text"}


def run_tests():
    global PASS, FAIL

    # Import server module and patch client
    import zep_cloud_server as srv
    srv.client = MockClient()

    # --- Test tool list ---
    tools = asyncio.run(srv.list_tools())
    expected_names = {
        "zep_store_memory", "zep_search_memory", "zep_get_memory",
        "zep_get_graph_nodes", "zep_get_graph_edges", "zep_get_node_details",
        "zep_get_thread_context",
    }
    actual_names = {t.name for t in tools}
    log(actual_names == expected_names, "Tool list matches", f"found={sorted(actual_names)}")

    # --- Test each tool has required schema fields ---
    for tool in tools:
        has_schema = tool.inputSchema is not None and "properties" in tool.inputSchema
        log(has_schema, f"Schema for {tool.name}")

    # --- Test tool dispatch ---

    # store_memory
    result = asyncio.run(srv.call_tool("zep_store_memory", {"session_id": "s1", "content": "hello"}))
    data = json.loads(result[0].text)
    log(data.get("success") is True, "Dispatch: zep_store_memory")

    # search_memory
    result = asyncio.run(srv.call_tool("zep_search_memory", {"query": "test"}))
    data = json.loads(result[0].text)
    log("edges" in data, "Dispatch: zep_search_memory")

    # get_memory
    result = asyncio.run(srv.call_tool("zep_get_memory", {"session_id": "s1"}))
    data = json.loads(result[0].text)
    log(data.get("message_count") == 2, "Dispatch: zep_get_memory")

    # get_memory with role_filter
    result = asyncio.run(srv.call_tool("zep_get_memory", {"session_id": "s1", "role_filter": "user"}))
    data = json.loads(result[0].text)
    log(data.get("message_count") == 1, "Dispatch: zep_get_memory (role_filter=user)", f"count={data.get('message_count')}")

    # get_graph_nodes
    result = asyncio.run(srv.call_tool("zep_get_graph_nodes", {}))
    data = json.loads(result[0].text)
    log(data.get("node_count") == 1, "Dispatch: zep_get_graph_nodes")

    # get_graph_edges
    result = asyncio.run(srv.call_tool("zep_get_graph_edges", {}))
    data = json.loads(result[0].text)
    log(data.get("edge_count") == 1, "Dispatch: zep_get_graph_edges")

    # get_node_details
    result = asyncio.run(srv.call_tool("zep_get_node_details", {"node_uuid": "n-1"}))
    data = json.loads(result[0].text)
    log(data.get("node", {}).get("name") == "Alice", "Dispatch: zep_get_node_details")

    # get_thread_context
    result = asyncio.run(srv.call_tool("zep_get_thread_context", {"session_id": "s1"}))
    data = json.loads(result[0].text)
    log(data.get("context") is not None, "Dispatch: zep_get_thread_context")

    # unknown tool
    result = asyncio.run(srv.call_tool("zep_unknown", {}))
    data = json.loads(result[0].text)
    log("error" in data, "Dispatch: unknown tool returns error")

    # --- Summary ---
    print(f"\n{'='*50}")
    print(f"Results: {PASS} passed, {FAIL} failed, {PASS + FAIL} total")
    if FAIL > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
