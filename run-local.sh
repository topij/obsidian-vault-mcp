#!/usr/bin/env bash
# Run the Obsidian vault MCP server locally against the iCloud vault.
# Usage: ./run-local.sh

set -euo pipefail

cd "$(dirname "$0")"

export OBSIDIAN_VAULT_PATH="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian-notes"
export MCP_HOST=127.0.0.1
export MCP_PORT=8002
export MCP_TRANSPORT=sse
export LOG_LEVEL=INFO

exec .venv/bin/python -m obsidian_vault_mcp.server
