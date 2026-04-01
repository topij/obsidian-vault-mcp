# Tools Reference

All tools are available via SSE transport at `http://<host>:8002/sse`.

## vault_list

List files in the vault matching a glob pattern.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | string | no | `""` (root) | Relative directory to search in |
| `pattern` | string | no | `"*.md"` | Glob pattern for filenames |
| `recursive` | bool | no | `true` | Include subdirectories |
| `limit` | int | no | `100` | Maximum results |

**Returns**: List of `{"path": str, "size": int, "modified": "ISO timestamp"}`

**Example**: "List all markdown files in 10-NOTES/"

## vault_read

Read a note with full parsing.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | string | yes | — | Relative path to the note |

**Returns**:

```json
{
  "path": "10-NOTES/transformers.md",
  "frontmatter": {"tags": ["ai", "ml"], "title": "Transformers"},
  "tags": ["ai", "ml", "attention"],
  "body": "The body text without frontmatter...",
  "wiki_links": ["attention-mechanism", "BERT"],
  "modified": "2026-03-15T10:30:00Z",
  "size": 2048
}
```

Tags are merged from YAML frontmatter and inline `#hashtags`, deduplicated and lowercased.

**Example**: "Read the note at 10-NOTES/transformers.md"

## vault_write

Create or overwrite a note. Uses atomic writes (temp file + rename).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | string | yes | — | Relative path for the note |
| `content` | string | yes | — | Full markdown content (include frontmatter if desired) |
| `allow_overwrite` | bool | no | `false` | Set `true` to replace existing file |

**Returns**: `{"path": str, "created": bool, "size": int}`

Creates parent directories automatically. Refuses to overwrite unless `allow_overwrite` is true.

**Example**: "Write a synthesis note to 20-SYNTHESIS/pricing-strategy.md"

## vault_search

Full-text search with context snippets. Case-insensitive substring matching.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | yes | — | Search string |
| `path` | string | no | `""` (all) | Limit to subdirectory |
| `limit` | int | no | `20` | Maximum matching files |

**Returns**: List of `{"path": str, "matches": [str]}` — up to 5 context lines per file.

**Example**: "Search my vault for mentions of transformer architecture"

## vault_search_by_tag

Find notes by frontmatter or inline tags.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `tags` | list[str] | yes | — | Tags to search for (e.g. `["ai", "meeting"]`) |
| `match_all` | bool | no | `true` | `true` = AND (all tags), `false` = OR (any tag) |
| `path` | string | no | `""` (all) | Limit to subdirectory |
| `limit` | int | no | `50` | Maximum results |

**Returns**: List of `{"path": str, "tags": [str], "modified": "ISO timestamp"}`

Tags are matched case-insensitively. Both YAML `tags:` frontmatter and inline `#hashtags` are searched.

**Example**: "Find all notes tagged with both 'ai' and 'project'"

## vault_recent

Recently modified notes, newest first.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `days` | int | no | `7` | Lookback window in days |
| `path` | string | no | `""` (all) | Limit to subdirectory |
| `limit` | int | no | `30` | Maximum results |

**Returns**: List of `{"path": str, "size": int, "modified": "ISO timestamp"}`

**Example**: "Show notes modified in the last 3 days"

## vault_move

Move or rename a note within the vault.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `source` | string | yes | — | Current relative path |
| `destination` | string | yes | — | New relative path |

**Returns**: `{"source": str, "destination": str}`

Creates destination parent directories as needed. Does NOT update wiki-links — Obsidian resolves links by filename, not path, so moves between directories don't break links.

**Example**: "Move 00-INBOX/draft-idea.md to 10-NOTES/idea.md"

## vault_structure

Folder tree with file counts and total size.

No parameters.

**Returns**:

```json
{
  "total_files": 1380,
  "total_size_mb": 14.4,
  "folders": [
    {"path": "00-INBOX", "files": 12},
    {"path": "10-NOTES", "files": 845},
    {"path": "10-NOTES/Learning", "files": 320},
    ...
  ]
}
```

Useful for understanding vault organization before searching or writing.

**Example**: "Show me the structure of my vault"

## vault_backlinks

Find notes that link to a given note via `[[wiki-links]]`.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `note_name` | string | yes | — | Note title (filename without `.md`) or relative path |
| `limit` | int | no | `50` | Maximum results |

**Returns**: List of `{"path": str, "matches": [str]}` — context lines containing the link.

Matching is case-insensitive on the filename part. Self-links are excluded.

**Example**: "What notes link to 'transformers'?"

## HTTP Endpoints

### GET /health

Health check. No authentication.

**Response**: `{"ok": true, "vault_path": "/app/vault", "files": 1380}`

### GET /sse

MCP SSE transport endpoint. Claude connects here for tool access.

## Excluded Directories

The following directories are always excluded from all operations:

`.obsidian/`, `.git/`, `.smart-env/`, `Trash/`, `assets/`, `node_modules/`
