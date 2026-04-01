# Architecture

## Overview

Three modules with clean separation of concerns:

```
server.py          MCP tools + HTTP routes (depends on FastMCP)
    ↓
vault.py           Filesystem operations (zero MCP dependencies)
    ↓
frontmatter.py     Markdown parsing (zero dependencies beyond PyYAML)
```

`vault.py` and `frontmatter.py` can be imported directly in other projects — they have no MCP dependencies.

## Why No Database

At ~1,400 files and 15 MB, a full vault scan takes under 1 second. Adding a database would mean:

- Keeping the database in sync with filesystem changes from Syncthing, Obsidian, or manual edits
- Handling conflicts when the file and database disagree
- More complexity for no measurable performance gain

The filesystem is the source of truth. When the vault grows past ~10,000 files and scans become slow, the right upgrade is a sidecar index (sqlite-vec for semantic search), not replacing the filesystem.

## Module Design

### frontmatter.py (136 lines)

Parses Markdown notes into structured data:

- **`parse_note(content)`** — Returns frontmatter dict, merged tags, body text, wiki-links
- **`extract_frontmatter(content)`** — YAML between `---` delimiters at file start
- **`extract_tags(frontmatter, body)`** — Merges YAML `tags`/`tag` key with inline `#hashtags`
- **`extract_wiki_links(content)`** — Extracts `[[target]]` and `[[target|display]]` links

Tag handling:
- Supports international characters (e.g., `#päätös`)
- Supports nested tags with slashes (`#project/ai-tool`)
- Negative lookbehind prevents matching anchor links (`[text](#anchor)`)
- All tags lowercased and deduplicated

### vault.py (433 lines)

All filesystem operations. Every function takes a `vault_root: Path` parameter and returns plain dicts/lists.

Key design decisions:

- **Path safety**: `_resolve_path()` validates that all paths resolve within `vault_root`. Blocks `../../etc/passwd` style traversals.
- **Atomic writes**: `write_note()` writes to a temp file in the same directory, then uses `os.replace()` for an atomic rename. This prevents partial writes that could confuse Syncthing.
- **Excluded directories**: `.obsidian/`, `.git/`, `.smart-env/`, `Trash/`, `assets/`, `node_modules/` are skipped in all operations.
- **No caching**: Every operation reads from disk. At this vault size, caching would add complexity without benefit.

### server.py (275 lines)

Thin wrapper that maps vault operations to MCP tools. Each tool function calls the corresponding vault function and returns the result.

Environment-driven configuration (`OBSIDIAN_VAULT_PATH`, `MCP_HOST`, `MCP_PORT`, `MCP_TRANSPORT`, `LOG_LEVEL`).

## Syncthing Considerations

The vault is synced between Mac (primary editing) and CT 104 (headless MCP server) via Syncthing:

```
Mac (Obsidian app) ←── Syncthing ──→ CT 104 (/root/obsidian-vault)
                                         ↑
                                    obsidian-vault-mcp reads/writes here
```

Atomic writes are critical — if the MCP server writes a half-finished file, Syncthing would propagate the corruption to the Mac. `os.replace()` is atomic on Linux and macOS, so Syncthing only ever sees complete files.

Syncthing's conflict detection creates `.sync-conflict` files if both sides edit simultaneously. In practice this is rare since synthesis sessions and manual editing don't overlap.

## Docker Deployment

```
docker-compose.yml
├── mcp-server (python:3.12-slim + uv)
│   ├── Vault: bind-mounted from host
│   ├── User: configurable UID/GID via APP_UID/APP_GID build args
│   ├── Health check: GET /health
│   └── Resource limit: 256 MB, 0.5 CPU
└── cloudflared (cloudflare/cloudflared:2025.2.1)
    ├── Protocol: http2 (required for LXC)
    └── Resource limit: 128 MB, 0.5 CPU
```

The `APP_UID`/`APP_GID` build args match the vault file ownership on the host. On CT 104 where Syncthing runs as root, these default to 0. On other hosts, set them to match your user.

## Testing

60+ tests across two files:

- **test_vault.py** — File listing, reading, writing, searching, tag search, recent files, moving, structure, backlinks. Includes path traversal security tests.
- **test_frontmatter.py** — YAML parsing, tag extraction (all formats), wiki-link extraction, international characters, nested tags.

All tests use `tmp_path` fixtures — no real vault needed.
