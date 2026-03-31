# obsidian-vault-mcp

A headless MCP server that reads your Obsidian vault directly — no Obsidian app, no REST API plugin needed.

Built with [FastMCP](https://github.com/jlowin/fastmcp). Designed for headless operation on servers where Obsidian isn't running.

## Features

- **Direct filesystem access** — reads/writes markdown files on disk
- **Frontmatter + tag parsing** — handles YAML frontmatter and inline `#hashtags`
- **Wiki-link support** — extracts `[[links]]` and finds backlinks
- **Full-text search** — case-insensitive substring search with context
- **Headless** — no Obsidian app or plugins required
- **Docker-ready** — bind-mount your vault and go

## MCP Tools

| Tool | Description |
|------|-------------|
| `vault_list` | List files with glob pattern |
| `vault_read` | Read note with parsed frontmatter, tags, wiki-links |
| `vault_write` | Create/overwrite note (atomic writes) |
| `vault_search` | Full-text search with context snippets |
| `vault_search_by_tag` | Find notes by tags |
| `vault_recent` | Recently modified notes |
| `vault_move` | Move/rename a note |
| `vault_structure` | Folder tree with file counts |
| `vault_backlinks` | Find notes linking to a given note |

## Quick Start

### Local (for development)

```bash
# Point at your vault
export OBSIDIAN_VAULT_PATH="$HOME/path/to/your/vault"

# Run with SSE transport
uv run python -m obsidian_vault_mcp.server
```

Then add to Claude Code:

```bash
claude mcp add --transport sse obsidian http://127.0.0.1:8002/sse
```

### Docker

```bash
docker compose up -d --build
```

The vault directory is bind-mounted from the host (configured in `docker-compose.yml`).

## Reusable Modules

The core modules have **zero MCP dependencies** and can be imported in other projects:

```python
from obsidian_vault_mcp.vault import read_note, search_notes, get_structure
from obsidian_vault_mcp.frontmatter import parse_note, extract_tags
```

## License

MIT
