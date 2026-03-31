"""Obsidian vault MCP server — tools for reading, writing, and searching vault files."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from obsidian_vault_mcp import vault

VAULT_PATH = Path(os.environ.get("OBSIDIAN_VAULT_PATH", "/app/vault"))

mcp = FastMCP(
    "obsidian",
    host=os.environ.get("MCP_HOST", "127.0.0.1"),
    port=int(os.environ.get("MCP_PORT", "8002")),
)

logger = logging.getLogger("obsidian_vault_mcp")


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def _setup_logging() -> None:
    """Configure logging to stderr so stdout remains free for MCP stdio protocol."""
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(line_buffering=True)
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )
    logging.getLogger("mcp").setLevel(logging.WARNING)
    logging.getLogger("obsidian_vault_mcp").setLevel(logging.DEBUG)


# ---------------------------------------------------------------------------
# MCP tools
# ---------------------------------------------------------------------------


@mcp.tool()
def vault_list(
    path: str = "",
    pattern: str = "*.md",
    recursive: bool = True,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List files in the vault.

    Args:
        path: Relative directory path (e.g. "10-NOTES/daily-notes"). Empty = vault root.
        pattern: Glob pattern to match filenames (default: "*.md").
        recursive: Include subdirectories (default: True).
        limit: Maximum number of results (default: 100).
    """
    logger.info("vault_list path=%r pattern=%r recursive=%s limit=%d", path, pattern, recursive, limit)
    results = vault.list_files(VAULT_PATH, path=path, pattern=pattern, recursive=recursive, limit=limit)
    logger.info("vault_list returned %d file(s)", len(results))
    return results


@mcp.tool()
def vault_read(path: str) -> dict[str, Any]:
    """Read a note from the vault.

    Returns the note's parsed frontmatter, merged tags (from YAML and inline #hashtags),
    body text, wiki-links, modification time, and file size.

    Args:
        path: Relative path to the note (e.g. "10-NOTES/Learning/AI/transformers.md").
    """
    logger.info("vault_read path=%r", path)
    result = vault.read_note(VAULT_PATH, path)
    logger.info("vault_read returned %d bytes", result["size"])
    return result


@mcp.tool()
def vault_write(
    path: str,
    content: str,
    allow_overwrite: bool = False,
) -> dict[str, Any]:
    """Create or overwrite a note in the vault.

    Writes atomically (temp file + rename) to prevent partial writes.
    Creates parent directories as needed.

    Args:
        path: Relative path for the note (e.g. "30-SYNTHESIS/topic.md").
        content: Full markdown content (including frontmatter if desired).
        allow_overwrite: Set True to replace an existing file (default: False).
    """
    logger.info("vault_write path=%r allow_overwrite=%s content_len=%d", path, allow_overwrite, len(content))
    result = vault.write_note(VAULT_PATH, path=path, content=content, allow_overwrite=allow_overwrite)
    logger.info("vault_write %s path=%r size=%d", "created" if result["created"] else "overwritten", path, result["size"])
    return result


@mcp.tool()
def vault_search(
    query: str,
    path: str = "",
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Full-text search across vault notes.

    Case-insensitive substring search. Returns matching notes with
    context snippets (up to 5 matching lines per file).

    Args:
        query: Search string.
        path: Limit search to this subdirectory (e.g. "10-NOTES"). Empty = entire vault.
        limit: Maximum number of matching files (default: 20).
    """
    logger.info("vault_search query=%r path=%r limit=%d", query[:80], path, limit)
    results = vault.search_notes(VAULT_PATH, query=query, path=path, limit=limit)
    logger.info("vault_search returned %d result(s)", len(results))
    return results


@mcp.tool()
def vault_search_by_tag(
    tags: list[str],
    match_all: bool = True,
    path: str = "",
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Find notes by tags (from YAML frontmatter or inline #hashtags).

    Args:
        tags: Tags to search for (e.g. ["meeting", "ai"]).
        match_all: If True, note must have ALL specified tags. If False, ANY tag matches.
        path: Limit to subdirectory. Empty = entire vault.
        limit: Maximum results (default: 50).
    """
    logger.info("vault_search_by_tag tags=%r match_all=%s path=%r", tags, match_all, path)
    results = vault.search_by_tag(VAULT_PATH, tags=tags, match_all=match_all, path=path, limit=limit)
    logger.info("vault_search_by_tag returned %d result(s)", len(results))
    return results


@mcp.tool()
def vault_recent(
    days: int = 7,
    path: str = "",
    limit: int = 30,
) -> list[dict[str, Any]]:
    """List recently modified notes, newest first.

    Args:
        days: Look back this many days (default: 7).
        path: Limit to subdirectory. Empty = entire vault.
        limit: Maximum results (default: 30).
    """
    logger.info("vault_recent days=%d path=%r limit=%d", days, path, limit)
    results = vault.recent_notes(VAULT_PATH, days=days, path=path, limit=limit)
    logger.info("vault_recent returned %d result(s)", len(results))
    return results


@mcp.tool()
def vault_move(
    source: str,
    destination: str,
) -> dict[str, Any]:
    """Move or rename a note in the vault.

    Does NOT update wiki-links — Obsidian resolves links by filename (not path),
    so moving a file between directories doesn't break links.

    Args:
        source: Current relative path.
        destination: New relative path.
    """
    logger.info("vault_move source=%r destination=%r", source, destination)
    result = vault.move_note(VAULT_PATH, source=source, destination=destination)
    logger.info("vault_move done: %s -> %s", result["source"], result["destination"])
    return result


@mcp.tool()
def vault_structure() -> dict[str, Any]:
    """Return the vault folder tree with file counts at each level.

    Shows total files, total size, and per-folder breakdown. Useful for
    understanding vault organization before searching or writing.
    """
    logger.info("vault_structure")
    result = vault.get_structure(VAULT_PATH)
    logger.info("vault_structure total_files=%d total_size_mb=%.1f", result["total_files"], result["total_size_mb"])
    return result


@mcp.tool()
def vault_backlinks(
    note_name: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Find all notes that contain [[wiki-links]] pointing to a given note.

    Args:
        note_name: Note title (filename without .md) or relative path.
                   Matching is case-insensitive on the filename part.
        limit: Maximum results (default: 50).
    """
    logger.info("vault_backlinks note_name=%r limit=%d", note_name, limit)
    results = vault.get_backlinks(VAULT_PATH, note_name=note_name, limit=limit)
    logger.info("vault_backlinks returned %d result(s)", len(results))
    return results


# ---------------------------------------------------------------------------
# Custom HTTP routes
# ---------------------------------------------------------------------------


@mcp.custom_route("/health", methods=["GET"])
async def http_health(request: Request) -> JSONResponse:
    """Health check — no auth required."""
    file_count = vault.count_files(VAULT_PATH)
    return JSONResponse({
        "ok": True,
        "vault_path": str(VAULT_PATH),
        "files": file_count,
    })


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    _setup_logging()
    logger.info("Obsidian vault MCP server starting")

    if not VAULT_PATH.is_dir():
        logger.error("Vault path does not exist: %s", VAULT_PATH)
        sys.exit(1)

    file_count = vault.count_files(VAULT_PATH)
    transport = os.environ.get("MCP_TRANSPORT", "sse")
    host = os.environ.get("MCP_HOST", "127.0.0.1")
    port = os.environ.get("MCP_PORT", "8002")

    print("", file=sys.stderr, flush=True)
    print("  Obsidian Vault MCP — ready for tool calls", file=sys.stderr, flush=True)
    print(f"  Vault: {VAULT_PATH} ({file_count} files)", file=sys.stderr, flush=True)
    print("  Tools: vault_list, vault_read, vault_write, vault_search,", file=sys.stderr, flush=True)
    print("         vault_search_by_tag, vault_recent, vault_move,", file=sys.stderr, flush=True)
    print("         vault_structure, vault_backlinks", file=sys.stderr, flush=True)
    print(f"  HTTP:  GET /health", file=sys.stderr, flush=True)
    if transport == "sse":
        print(f"  Transport: SSE ({host}:{port})", file=sys.stderr, flush=True)
    else:
        print("  Transport: stdio", file=sys.stderr, flush=True)
    print("", file=sys.stderr, flush=True)

    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
