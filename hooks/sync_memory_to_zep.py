#!/usr/bin/env python3
"""
PostToolUse hook: sync Claude Code auto-memory writes to Zep Cloud.

Receives PostToolUse JSON on stdin. If the tool wrote to a memory/*.md file
and ZEP_API_KEY + ZEP_USER_ID are set, stores the file content as a Zep thread message.

Never raises — all errors go to stderr and exit 0 to avoid blocking Claude Code.
"""

import json
import os
import sys


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception as e:
        print(f"sync_memory_to_zep: failed to parse stdin: {e}", file=sys.stderr)
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}

    # Only handle Write and Edit tool calls
    if tool_name not in ("Write", "Edit"):
        sys.exit(0)

    file_path = tool_input.get("file_path", "")

    # Only sync files inside a memory/ directory with .md extension
    import fnmatch
    if not fnmatch.fnmatch(file_path, "*/memory/*.md"):
        sys.exit(0)

    api_key = os.environ.get("ZEP_API_KEY")
    user_id = os.environ.get("ZEP_USER_ID")

    if not api_key or not user_id:
        # Silently skip — user hasn't configured the hook
        sys.exit(0)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"sync_memory_to_zep: could not read {file_path}: {e}", file=sys.stderr)
        sys.exit(0)

    if not content.strip():
        sys.exit(0)

    try:
        from zep_cloud import Zep, Message
    except ImportError:
        print(
            "sync_memory_to_zep: zep-cloud not installed. Run: pip install zep-cloud",
            file=sys.stderr,
        )
        sys.exit(0)

    try:
        client = Zep(api_key=api_key)
        session_id = f"claude_code_memory_{user_id}"

        # Idempotent user + thread creation
        try:
            client.user.add(user_id=user_id)
        except Exception:
            pass

        try:
            client.thread.create(thread_id=session_id, user_id=user_id)
        except Exception:
            pass

        client.thread.add_messages(
            thread_id=session_id,
            messages=[
                Message(
                    content=content,
                    role="system",
                    metadata={"source_file": file_path},
                )
            ],
        )
    except Exception as e:
        print(f"sync_memory_to_zep: error syncing to Zep: {e}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
