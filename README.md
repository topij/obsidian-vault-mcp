# obsidian-vault-mcp

A headless MCP server for Obsidian vaults. Reads and writes Markdown files directly on the filesystem — no Obsidian app, no REST API plugin needed.

Built with [FastMCP](https://github.com/modelcontextprotocol/python-sdk). Designed for server environments where Obsidian isn't running.

## Features

- **Direct filesystem access** — reads/writes Markdown files on disk
- **Frontmatter + tag parsing** — YAML frontmatter and inline `#hashtags` (including international characters and nested tags like `#project/ai`)
- **Wiki-link support** — extracts `[[links]]` and finds backlinks
- **Full-text search** — case-insensitive substring search with context snippets
- **Atomic writes** — temp file + `os.replace()` prevents corruption (safe for Syncthing)
- **Path security** — validates all paths stay within vault root
- **Headless** — no Obsidian app or plugins required
- **Docker-ready** — bind-mount your vault and go
- **9 MCP tools** — list, read, write, search, tag search, recent, move, structure, backlinks

## Quick Start

### Local

```bash
export OBSIDIAN_VAULT_PATH="$HOME/path/to/your/vault"
uv run python -m obsidian_vault_mcp.server
```

Connect to Claude Code:

```bash
claude mcp add --transport sse obsidian http://127.0.0.1:8002/sse
```

### Docker

```bash
docker compose up -d --build
```

The vault directory is bind-mounted from the host (configured in `docker-compose.yml`).

## MCP Tools

| Tool | Description |
|------|-------------|
| `vault_list` | List files with glob pattern matching |
| `vault_read` | Read note with parsed frontmatter, tags, wiki-links |
| `vault_write` | Create/overwrite note (atomic writes) |
| `vault_search` | Full-text search with context snippets |
| `vault_search_by_tag` | Find notes by frontmatter or inline tags |
| `vault_recent` | Recently modified notes |
| `vault_move` | Move/rename a note |
| `vault_structure` | Folder tree with file counts and sizes |
| `vault_backlinks` | Find notes linking to a given note |

## Documentation

| Document | Description |
|----------|-------------|
| [Getting Started](docs/getting-started.md) | Setup, configuration, first tool calls |
| [Tools Reference](docs/tools-reference.md) | Full parameters and return values for all 9 tools |
| [Architecture](docs/architecture.md) | Design decisions, module structure, Syncthing considerations |

## Reusable Modules

The core modules have **zero MCP dependencies** and can be imported directly:

```python
from obsidian_vault_mcp.vault import read_note, search_notes, get_structure
from obsidian_vault_mcp.frontmatter import parse_note, extract_tags
```

## Part of the Knowledge System

This server is one of three stores in the [home server knowledge system](../docs/knowledge-system/README.md). It handles developed notes while [Voice Notes](../mcp-voice-notes/) handles voice memos and [Brain](../brain/) handles quick text captures.

It works fully standalone — you don't need the other components. Just point it at any Obsidian vault.

## License

MIT
