# Getting Started

## Prerequisites

- Python 3.12+ with [uv](https://docs.astral.sh/uv/)
- An Obsidian vault (any directory of Markdown files works)
- Optional: Docker for containerized deployment

## Local Setup

### 1. Clone and install

```bash
git clone https://github.com/topij/obsidian-vault-mcp.git
cd obsidian-vault-mcp
uv sync
```

### 2. Point at your vault

```bash
export OBSIDIAN_VAULT_PATH="$HOME/path/to/your/vault"
```

Or create a `.env` file:

```ini
OBSIDIAN_VAULT_PATH=/Users/you/Documents/vault
MCP_HOST=127.0.0.1
MCP_PORT=8002
LOG_LEVEL=INFO
```

### 3. Start the server

```bash
uv run python -m obsidian_vault_mcp.server
```

You should see:

```
  Obsidian Vault MCP — ready for tool calls
  Vault: /Users/you/Documents/vault (1380 files)
  Tools: vault_list, vault_read, vault_write, vault_search, ...
  Transport: SSE (127.0.0.1:8002)
```

### 4. Connect to Claude

**Claude Code**:

```bash
claude mcp add --transport sse obsidian http://127.0.0.1:8002/sse
```

**Claude Desktop** (Settings > Developer > Edit Config):

```json
{
  "mcpServers": {
    "obsidian": {
      "url": "http://127.0.0.1:8002/sse"
    }
  }
}
```

### 5. Try it out

Ask Claude:

```
Show me the structure of my Obsidian vault.
```

Claude calls `vault_structure` and shows you the folder tree with file counts.

```
Find notes about machine learning in my vault.
```

Claude calls `vault_search` and returns matching notes with context snippets.

```
Read the note at 10-NOTES/transformers.md
```

Claude calls `vault_read` and returns the note's frontmatter, body, tags, and wiki-links.

## Docker Setup

For server deployment (e.g., on a NUC or cloud host where Obsidian isn't running):

```bash
cp .env.example .env
# Edit .env: set OBSIDIAN_TUNNEL_TOKEN if using Cloudflare Tunnel

docker compose up -d --build
```

The vault is bind-mounted from the host. In `docker-compose.yml`:

```yaml
volumes:
  - /root/obsidian-vault:/app/vault:rw
```

Adjust the host path to wherever your vault lives.

**Health check**:

```bash
curl http://localhost:8002/health
# {"ok": true, "vault_path": "/app/vault", "files": 1380}
```

## Running as a LaunchAgent (macOS)

For persistent local operation on Mac:

```bash
./run-local.sh
```

Or create a LaunchAgent in `~/Library/LaunchAgents/com.user.obsidian-vault-mcp.plist` that runs the server on login.

## Running Tests

```bash
uv sync --dev
uv run pytest tests/ -v
```

60+ tests covering vault operations, frontmatter parsing, path security, and edge cases.

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `OBSIDIAN_VAULT_PATH` | `/app/vault` | Path to the vault directory |
| `MCP_HOST` | `127.0.0.1` | Server bind address |
| `MCP_PORT` | `8002` | Server port |
| `MCP_TRANSPORT` | `sse` | Transport type (`sse` or `stdio`) |
| `LOG_LEVEL` | `INFO` | Logging level |

## Next Steps

- [Tools Reference](tools-reference.md) — full parameters and return values for all 9 tools
- [Architecture](architecture.md) — design decisions and module structure
