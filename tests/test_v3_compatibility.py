#!/usr/bin/env python3
"""
Integration tests for Zep Cloud v3 API.
Requires a valid ZEP_API_KEY environment variable.

Run: python tests/test_v3_compatibility.py
"""

import os
import sys
import time
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from zep_cloud_client import ZepCloudClient

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


def run_tests():
    global PASS, FAIL

    api_key = os.getenv("ZEP_API_KEY")
    if not api_key:
        print("ERROR: ZEP_API_KEY not set. Skipping integration tests.")
        sys.exit(1)

    # Initialize client
    try:
        client = ZepCloudClient(api_key=api_key)
        log(True, "Client initialization")
    except Exception as e:
        log(False, "Client initialization", str(e))
        sys.exit(1)

    # Use a unique session ID per test run to avoid collisions
    session_id = f"test-session-{uuid.uuid4().hex[:8]}"

    # --- Store Memory ---
    try:
        result = client.store_memory(
            session_id=session_id,
            content="The user's favorite color is blue.",
            role="assistant",
        )
        log(result.get("success") is True, "store_memory", f"thread={result.get('thread_id')}")
    except Exception as e:
        log(False, "store_memory", str(e))

    # Store a second message
    try:
        result = client.store_memory(
            session_id=session_id,
            content="What is my favorite color?",
            role="user",
        )
        log(result.get("success") is True, "store_memory (user msg)")
    except Exception as e:
        log(False, "store_memory (user msg)", str(e))

    # --- Get Memory ---
    try:
        result = client.get_memory(session_id=session_id)
        count = result.get("message_count", 0)
        log(count >= 2, "get_memory", f"message_count={count}")
    except Exception as e:
        log(False, "get_memory", str(e))

    # Get memory with lastn
    try:
        result = client.get_memory(session_id=session_id, lastn=1)
        count = result.get("message_count", 0)
        log(count == 1, "get_memory (lastn=1)", f"message_count={count}")
    except Exception as e:
        log(False, "get_memory (lastn=1)", str(e))

    # --- Search Graph ---
    # Note: graph indexing is async, so results may be empty for fresh data
    try:
        result = client.search_graph(query="favorite color", limit=5)
        log("edges" in result and "nodes" in result, "search_graph",
            f"edges={result.get('edge_count', 0)}, nodes={result.get('node_count', 0)}")
    except Exception as e:
        log(False, "search_graph", str(e))

    # --- Get Graph Nodes ---
    try:
        result = client.get_graph_nodes(limit=10)
        log("nodes" in result, "get_graph_nodes", f"count={result.get('node_count', 0)}")
    except Exception as e:
        log(False, "get_graph_nodes", str(e))

    # --- Get Graph Edges ---
    try:
        result = client.get_graph_edges(limit=10)
        log("edges" in result, "get_graph_edges", f"count={result.get('edge_count', 0)}")
    except Exception as e:
        log(False, "get_graph_edges", str(e))

    # --- Get Node Details (if nodes exist) ---
    try:
        nodes_result = client.get_graph_nodes(limit=1)
        nodes = nodes_result.get("nodes", [])
        if nodes:
            node_uuid = nodes[0]["uuid"]
            result = client.get_node_details(node_uuid=node_uuid)
            log("node" in result, "get_node_details",
                f"name={result['node'].get('name')}, edges={result.get('edge_count', 0)}")
        else:
            log(True, "get_node_details", "skipped (no nodes yet)")
    except Exception as e:
        log(False, "get_node_details", str(e))

    # --- Get Thread Context ---
    try:
        result = client.get_thread_context(session_id=session_id, mode="basic")
        log("context" in result, "get_thread_context", f"mode=basic, has_context={result.get('context') is not None}")
    except Exception as e:
        log(False, "get_thread_context", str(e))

    # --- Error Handling ---
    try:
        result = client.get_memory(session_id="nonexistent-thread-xyz-999")
        # Should either return empty or raise
        log(True, "get_memory (nonexistent thread)", "no crash")
    except Exception as e:
        log(True, "get_memory (nonexistent thread)", f"raised: {type(e).__name__}")

    # --- Summary ---
    print(f"\n{'='*50}")
    print(f"Results: {PASS} passed, {FAIL} failed, {PASS + FAIL} total")
    if FAIL > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
