"""Obsidian vault filesystem operations.

This module has no MCP dependencies — it works with pathlib.Path and returns
plain dicts/lists. It can be imported standalone for any project that needs
to read, write, or search an Obsidian vault on disk.
"""

from __future__ import annotations

import fnmatch
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from obsidian_vault_mcp.frontmatter import parse_note

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXCLUDED_DIRS = {".obsidian", ".git", ".smart-env", "Trash", "assets", "node_modules"}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _is_excluded(path: Path, vault_root: Path) -> bool:
    """Check if any component of the relative path is in EXCLUDED_DIRS."""
    try:
        rel = path.relative_to(vault_root)
    except ValueError:
        return True
    return any(part in EXCLUDED_DIRS for part in rel.parts)


def _resolve_path(vault_root: Path, relative: str) -> Path:
    """Resolve a relative vault path and validate it stays within the vault."""
    resolved = (vault_root / relative).resolve()
    vault_resolved = vault_root.resolve()
    if not str(resolved).startswith(str(vault_resolved) + os.sep) and resolved != vault_resolved:
        raise ValueError(f"Path escapes vault root: {relative}")
    return resolved


def _mtime_iso(path: Path) -> str:
    """Return file modification time as ISO 8601 string."""
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def _walk_md_files(vault_root: Path, subpath: str = "", recursive: bool = True) -> list[Path]:
    """Walk the vault and yield .md files, skipping excluded directories."""
    start = _resolve_path(vault_root, subpath) if subpath else vault_root.resolve()
    if not start.is_dir():
        return []

    results: list[Path] = []
    if recursive:
        for dirpath, dirnames, filenames in os.walk(start):
            dp = Path(dirpath)
            # Prune excluded dirs in-place so os.walk doesn't descend
            dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
            for f in filenames:
                if f.endswith(".md"):
                    results.append(dp / f)
    else:
        for f in start.iterdir():
            if f.is_file() and f.suffix == ".md" and not _is_excluded(f, vault_root):
                results.append(f)

    return results


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def list_files(
    vault_root: Path,
    path: str = "",
    pattern: str = "*.md",
    recursive: bool = True,
    limit: int = 100,
) -> list[dict]:
    """List files in the vault.

    Returns path, size, and modified time for each matching file.
    """
    start = _resolve_path(vault_root, path) if path else vault_root.resolve()
    if not start.is_dir():
        raise ValueError(f"Directory not found: {path}")

    results: list[dict] = []
    if recursive:
        for dirpath, dirnames, filenames in os.walk(start):
            dp = Path(dirpath)
            dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
            for f in sorted(filenames):
                fp = dp / f
                if fnmatch.fnmatch(f, pattern):
                    results.append({
                        "path": str(fp.relative_to(vault_root)),
                        "size": fp.stat().st_size,
                        "modified": _mtime_iso(fp),
                    })
                    if len(results) >= limit:
                        return results
    else:
        for fp in sorted(start.iterdir(), key=lambda p: p.name):
            if fp.is_file() and fnmatch.fnmatch(fp.name, pattern) and not _is_excluded(fp, vault_root):
                results.append({
                    "path": str(fp.relative_to(vault_root)),
                    "size": fp.stat().st_size,
                    "modified": _mtime_iso(fp),
                })
                if len(results) >= limit:
                    return results

    return results


def read_note(vault_root: Path, path: str) -> dict:
    """Read a note and return parsed content.

    Returns:
        {
            "path": str,
            "frontmatter": dict,
            "tags": list[str],
            "body": str,
            "wiki_links": list[str],
            "modified": str,
            "size": int,
        }
    """
    fp = _resolve_path(vault_root, path)
    if not fp.is_file():
        raise FileNotFoundError(f"Note not found: {path}")

    content = fp.read_text(encoding="utf-8")
    parsed = parse_note(content)

    return {
        "path": str(fp.relative_to(vault_root)),
        "modified": _mtime_iso(fp),
        "size": fp.stat().st_size,
        **parsed,
    }


def write_note(
    vault_root: Path,
    path: str,
    content: str,
    allow_overwrite: bool = False,
) -> dict:
    """Write a note to the vault atomically.

    Creates parent directories as needed. Refuses to overwrite existing
    files unless allow_overwrite is True.

    Returns:
        {"path": str, "created": bool, "size": int}
    """
    fp = _resolve_path(vault_root, path)
    created = not fp.exists()

    if fp.exists() and not allow_overwrite:
        raise FileExistsError(f"Note already exists (set allow_overwrite=True to replace): {path}")

    # Create parent directories
    fp.parent.mkdir(parents=True, exist_ok=True)

    # Atomic write: temp file in same directory, then rename
    fd, tmp_path = tempfile.mkstemp(dir=fp.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, fp)
    except Exception:
        # Clean up temp file on failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

    return {
        "path": str(fp.relative_to(vault_root)),
        "created": created,
        "size": fp.stat().st_size,
    }


def search_notes(
    vault_root: Path,
    query: str,
    path: str = "",
    limit: int = 20,
) -> list[dict]:
    """Case-insensitive full-text search across vault notes.

    Returns matching notes with context snippets (matching lines).
    """
    if not query:
        raise ValueError("query must not be empty")

    query_lower = query.lower()
    md_files = _walk_md_files(vault_root, path)
    results: list[dict] = []

    for fp in md_files:
        try:
            content = fp.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        content_lower = content.lower()
        if query_lower not in content_lower:
            continue

        # Collect matching lines with line numbers
        matches: list[dict] = []
        for i, line in enumerate(content.splitlines(), 1):
            if query_lower in line.lower():
                matches.append({"line": i, "text": line.strip()})
                if len(matches) >= 5:  # cap context per file
                    break

        results.append({
            "path": str(fp.relative_to(vault_root)),
            "matches": matches,
            "match_count": content_lower.count(query_lower),
        })

        if len(results) >= limit:
            break

    return results


def search_by_tag(
    vault_root: Path,
    tags: list[str],
    match_all: bool = True,
    path: str = "",
    limit: int = 50,
) -> list[dict]:
    """Find notes by tags (from frontmatter or inline #hashtags).

    Args:
        tags: Tags to search for.
        match_all: If True, note must have ALL tags. If False, ANY tag matches.
    """
    if not tags:
        raise ValueError("tags must not be empty")

    search_tags = {t.lower() for t in tags}
    md_files = _walk_md_files(vault_root, path)
    results: list[dict] = []

    for fp in md_files:
        try:
            content = fp.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        parsed = parse_note(content)
        note_tags = set(parsed["tags"])

        if match_all:
            if not search_tags.issubset(note_tags):
                continue
        else:
            if not search_tags.intersection(note_tags):
                continue

        results.append({
            "path": str(fp.relative_to(vault_root)),
            "tags": parsed["tags"],
            "modified": _mtime_iso(fp),
        })

        if len(results) >= limit:
            break

    return results


def recent_notes(
    vault_root: Path,
    days: int = 7,
    path: str = "",
    limit: int = 30,
) -> list[dict]:
    """List recently modified notes, newest first."""
    cutoff = time.time() - (days * 86400)
    md_files = _walk_md_files(vault_root, path)

    recent: list[tuple[float, Path]] = []
    for fp in md_files:
        mtime = fp.stat().st_mtime
        if mtime >= cutoff:
            recent.append((mtime, fp))

    # Sort by mtime descending
    recent.sort(key=lambda x: x[0], reverse=True)

    return [
        {
            "path": str(fp.relative_to(vault_root)),
            "size": fp.stat().st_size,
            "modified": _mtime_iso(fp),
        }
        for _, fp in recent[:limit]
    ]


def move_note(vault_root: Path, source: str, destination: str) -> dict:
    """Move or rename a note.

    Does NOT update wiki-links — Obsidian resolves links by filename, so
    moving a file to a different directory doesn't break links. Renaming
    the filename itself is better handled by Obsidian's built-in refactoring.
    """
    src = _resolve_path(vault_root, source)
    dst = _resolve_path(vault_root, destination)

    if not src.is_file():
        raise FileNotFoundError(f"Source not found: {source}")
    if dst.exists():
        raise FileExistsError(f"Destination already exists: {destination}")

    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)

    return {
        "source": source,
        "destination": str(dst.relative_to(vault_root)),
    }


def get_structure(vault_root: Path) -> dict:
    """Return the vault folder tree with file counts at each level."""
    vault_resolved = vault_root.resolve()
    total_files = 0
    total_size = 0
    folders: dict[str, dict] = {}

    for dirpath, dirnames, filenames in os.walk(vault_resolved):
        dp = Path(dirpath)
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]

        rel = str(dp.relative_to(vault_resolved))
        if rel == ".":
            rel = ""

        md_files = [f for f in filenames if f.endswith(".md")]
        if not md_files and not dirnames:
            continue

        file_count = len(md_files)
        dir_size = sum((dp / f).stat().st_size for f in md_files)
        total_files += file_count
        total_size += dir_size

        if rel:  # Skip root level — it goes into top-level counts
            folders[rel] = {"files": file_count, "size_bytes": dir_size}

    return {
        "total_files": total_files,
        "total_size_mb": round(total_size / (1024 * 1024), 1),
        "folders": folders,
    }


def get_backlinks(vault_root: Path, note_name: str, limit: int = 50) -> list[dict]:
    """Find all notes containing [[wiki-links]] pointing to the given note.

    Args:
        note_name: Note title (filename without .md) or relative path.
                   Matching is case-insensitive on the filename part.
    """
    # Normalize: strip .md extension and path, keep just the name
    target = Path(note_name).stem.lower()

    md_files = _walk_md_files(vault_root)
    results: list[dict] = []

    for fp in md_files:
        # Don't report self-links
        if fp.stem.lower() == target:
            continue

        try:
            content = fp.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        parsed = parse_note(content)
        matching_links = [
            link for link in parsed["wiki_links"]
            if Path(link).stem.lower() == target
        ]

        if not matching_links:
            continue

        # Extract a context line around the first link
        context = ""
        for line in content.splitlines():
            if f"[[{matching_links[0]}" in line:
                context = line.strip()
                break

        results.append({
            "path": str(fp.relative_to(vault_root)),
            "link_context": context,
        })

        if len(results) >= limit:
            break

    return results


def count_files(vault_root: Path) -> int:
    """Count total .md files in the vault (excluding excluded dirs)."""
    return len(_walk_md_files(vault_root))
