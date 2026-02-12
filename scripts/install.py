#!/usr/bin/env python3
"""
Automated setup script for mcp-server-zep-cloud.
Installs the package, prompts for API key, and configures Claude Desktop.

Run: python scripts/install.py
"""

import json
import os
import platform
import subprocess
import sys


def check_python_version():
    if sys.version_info < (3, 9):
        print(f"Error: Python 3.9+ is required (you have {sys.version})")
        sys.exit(1)
    print(f"Python {sys.version_info.major}.{sys.version_info.minor} — OK")


def install_package():
    print("\nInstalling mcp-server-zep-cloud...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "."],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    if result.returncode != 0:
        print("Error: pip install failed")
        sys.exit(1)
    print("Package installed successfully")


def prompt_api_key():
    print("\nYou need a Zep Cloud API key.")
    print("Get one at: https://app.getzep.com/")
    key = input("\nPaste your ZEP_API_KEY: ").strip()
    if not key:
        print("Warning: No API key provided. You can set ZEP_API_KEY later.")
    return key


def get_claude_desktop_config_path():
    system = platform.system()
    if system == "Darwin":
        return os.path.expanduser("~/Library/Application Support/Claude/claude_desktop_config.json")
    elif system == "Windows":
        return os.path.join(os.environ.get("APPDATA", ""), "Claude", "claude_desktop_config.json")
    else:
        print(f"Note: Claude Desktop config auto-setup not supported on {system}.")
        return None


def configure_claude_desktop(api_key):
    config_path = get_claude_desktop_config_path()
    if config_path is None:
        print_manual_config(api_key)
        return

    print(f"\nClaude Desktop config: {config_path}")

    config = {}
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                print("Warning: Existing config file is invalid JSON. Creating new one.")
                config = {}

    if "mcpServers" not in config:
        config["mcpServers"] = {}

    config["mcpServers"]["zep-cloud"] = {
        "command": "mcp-server-zep-cloud",
        "env": {
            "ZEP_API_KEY": api_key or "YOUR_API_KEY_HERE",
        },
    }

    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print("Claude Desktop configured successfully")


def print_manual_config(api_key):
    key_display = api_key or "YOUR_API_KEY_HERE"
    print("\nAdd this to your Claude Desktop config:")
    print(json.dumps({
        "mcpServers": {
            "zep-cloud": {
                "command": "mcp-server-zep-cloud",
                "env": {"ZEP_API_KEY": key_display},
            }
        }
    }, indent=2))


def main():
    print("=== mcp-server-zep-cloud Setup ===\n")

    check_python_version()
    install_package()
    api_key = prompt_api_key()
    configure_claude_desktop(api_key)

    print("\n=== Setup Complete ===")
    print("Restart Claude Desktop to start using Zep memory.")
    print("\nFor Claude Code CLI, run:")
    key_display = api_key or "YOUR_API_KEY_HERE"
    print(f'  claude mcp add zep-cloud -e ZEP_API_KEY={key_display} -- mcp-server-zep-cloud')


if __name__ == "__main__":
    main()
