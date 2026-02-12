#!/usr/bin/env python3
"""
Zep Cloud Client (v3)
Wraps the zep-cloud SDK v3 for thread-based memory management and knowledge graph operations.
"""

import os
import logging
from typing import Dict, List, Optional, Any

from dotenv import load_dotenv

try:
    from zep_cloud import Zep, Message
except ImportError:
    raise ImportError("zep-cloud SDK not found. Install with: pip install 'zep-cloud>=3.16.0'")

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_USER_ID = "default_user"


class ZepCloudClient:
    """Client for interacting with Zep Cloud API v3."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ZEP_API_KEY")
        if not self.api_key:
            raise ValueError("ZEP_API_KEY environment variable not set")

        self.client = Zep(api_key=self.api_key)
        self.user_id = DEFAULT_USER_ID
        self._ensure_user()
        logger.info("Zep Cloud client initialized (v3)")

    def _ensure_user(self):
        """Create the default user if it doesn't exist."""
        try:
            self.client.user.add(user_id=self.user_id)
            logger.info(f"Created user: {self.user_id}")
        except Exception:
            logger.debug(f"User {self.user_id} already exists")

    def _ensure_thread(self, thread_id: str):
        """Create a thread if it doesn't exist."""
        try:
            self.client.thread.create(thread_id=thread_id, user_id=self.user_id)
            logger.info(f"Created thread: {thread_id}")
        except Exception:
            logger.debug(f"Thread {thread_id} already exists")

    # --- Thread Operations ---

    def store_memory(
        self,
        session_id: str,
        content: str,
        role: str = "assistant",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Store content as a message in a thread."""
        self._ensure_thread(session_id)
        messages = [Message(content=content, role=role, metadata=metadata)]
        self.client.thread.add_messages(thread_id=session_id, messages=messages)
        return {
            "success": True,
            "thread_id": session_id,
            "role": role,
            "content_length": len(content),
        }

    def get_memory(
        self,
        session_id: str,
        lastn: Optional[int] = None,
        limit: Optional[int] = None,
        cursor: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get messages from a thread."""
        kwargs: Dict[str, Any] = {"thread_id": session_id}
        if lastn is not None:
            kwargs["lastn"] = lastn
        if limit is not None:
            kwargs["limit"] = limit
        if cursor is not None:
            kwargs["cursor"] = cursor

        response = self.client.thread.get(**kwargs)
        messages = []
        for msg in response.messages or []:
            messages.append({
                "uuid": getattr(msg, "uuid_", None) or getattr(msg, "uuid", None),
                "role": msg.role,
                "content": msg.content,
                "created_at": str(msg.created_at) if hasattr(msg, "created_at") and msg.created_at else None,
                "metadata": msg.metadata if hasattr(msg, "metadata") else None,
            })
        return {
            "thread_id": session_id,
            "message_count": len(messages),
            "messages": messages,
        }

    def get_thread_context(self, session_id: str, mode: str = "summary") -> Dict[str, Any]:
        """Get cross-thread context for a session."""
        self._ensure_thread(session_id)
        context = self.client.thread.get_user_context(thread_id=session_id, mode=mode)
        return {
            "thread_id": session_id,
            "mode": mode,
            "context": getattr(context, "context", None),
        }

    # --- Graph Operations ---

    def search_graph(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search the user's knowledge graph."""
        results = self.client.graph.search(
            query=query,
            user_id=self.user_id,
            limit=limit,
        )

        edges = []
        for edge in results.edges or []:
            edges.append({
                "uuid": getattr(edge, "uuid_", None) or getattr(edge, "uuid", None),
                "fact": getattr(edge, "fact", None),
                "name": getattr(edge, "name", None),
                "score": getattr(edge, "score", None),
                "created_at": str(edge.created_at) if hasattr(edge, "created_at") and edge.created_at else None,
            })

        nodes = []
        for node in results.nodes or []:
            nodes.append({
                "uuid": getattr(node, "uuid_", None) or getattr(node, "uuid", None),
                "name": getattr(node, "name", None),
                "labels": getattr(node, "labels", []),
                "summary": getattr(node, "summary", None),
                "score": getattr(node, "score", None),
            })

        return {
            "query": query,
            "edge_count": len(edges),
            "node_count": len(nodes),
            "edges": edges,
            "nodes": nodes,
        }

    def get_graph_nodes(self, limit: int = 50) -> Dict[str, Any]:
        """Get all nodes from the user's knowledge graph."""
        nodes_list = self.client.graph.node.get_by_user_id(
            user_id=self.user_id,
            limit=limit,
        )

        nodes = []
        for node in nodes_list or []:
            nodes.append({
                "uuid": getattr(node, "uuid_", None) or getattr(node, "uuid", None),
                "name": getattr(node, "name", None),
                "labels": getattr(node, "labels", []),
                "summary": getattr(node, "summary", None),
                "created_at": str(node.created_at) if hasattr(node, "created_at") and node.created_at else None,
            })

        return {"node_count": len(nodes), "nodes": nodes}

    def get_graph_edges(self, limit: int = 50) -> Dict[str, Any]:
        """Get all edges (relationships) from the user's knowledge graph."""
        edges_list = self.client.graph.edge.get_by_user_id(
            user_id=self.user_id,
            limit=limit,
        )

        edges = []
        for edge in edges_list or []:
            edges.append({
                "uuid": getattr(edge, "uuid_", None) or getattr(edge, "uuid", None),
                "fact": getattr(edge, "fact", None),
                "name": getattr(edge, "name", None),
                "source_node_uuid": getattr(edge, "source_node_uuid", None),
                "target_node_uuid": getattr(edge, "target_node_uuid", None),
                "created_at": str(edge.created_at) if hasattr(edge, "created_at") and edge.created_at else None,
            })

        return {"edge_count": len(edges), "edges": edges}

    def get_node_details(self, node_uuid: str) -> Dict[str, Any]:
        """Get detailed info about a specific node, including its edges and episodes."""
        node = self.client.graph.node.get(uuid_=node_uuid)
        edges_list = self.client.graph.node.get_edges(node_uuid=node_uuid)
        episodes_response = self.client.graph.node.get_episodes(node_uuid=node_uuid)

        node_data = {
            "uuid": getattr(node, "uuid_", None) or getattr(node, "uuid", None),
            "name": getattr(node, "name", None),
            "labels": getattr(node, "labels", []),
            "summary": getattr(node, "summary", None),
            "attributes": getattr(node, "attributes", {}),
            "created_at": str(node.created_at) if hasattr(node, "created_at") and node.created_at else None,
        }

        edges = []
        for edge in edges_list or []:
            edges.append({
                "uuid": getattr(edge, "uuid_", None) or getattr(edge, "uuid", None),
                "fact": getattr(edge, "fact", None),
                "name": getattr(edge, "name", None),
                "source_node_uuid": getattr(edge, "source_node_uuid", None),
                "target_node_uuid": getattr(edge, "target_node_uuid", None),
            })

        episodes = []
        episode_list = getattr(episodes_response, "episodes", []) or []
        for ep in episode_list:
            episodes.append({
                "uuid": getattr(ep, "uuid_", None) or getattr(ep, "uuid", None),
                "content": getattr(ep, "content", None),
                "created_at": str(ep.created_at) if hasattr(ep, "created_at") and ep.created_at else None,
            })

        return {
            "node": node_data,
            "edge_count": len(edges),
            "edges": edges,
            "episode_count": len(episodes),
            "episodes": episodes,
        }
