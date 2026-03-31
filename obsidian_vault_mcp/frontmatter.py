"""Parse Obsidian note content: YAML frontmatter, inline tags, and wiki-links.

This module has no MCP dependencies — it works with plain strings and dicts.
It can be imported standalone for any project that needs to parse Obsidian-style
markdown files.
"""

from __future__ import annotations

import re

import yaml

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# YAML frontmatter delimited by --- at the start of the file
_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.DOTALL)

# Inline hashtags: #tag-name (must start with a letter, allows letters/digits/hyphens/underscores)
# Negative lookbehind for [ prevents matching inside markdown links like [text](#anchor)
_INLINE_TAG_RE = re.compile(r"(?<!\[)(?:^|\s)#([a-zA-ZÀ-ÿ][a-zA-ZÀ-ÿ0-9_/-]*)", re.MULTILINE)

# Wiki-links: [[target]] or [[target|display text]]
_WIKI_LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_note(content: str) -> dict:
    """Parse a note into its components.

    Returns:
        {
            "frontmatter": dict,       # parsed YAML (empty dict if none)
            "tags": list[str],         # merged from frontmatter + inline, deduplicated
            "body": str,               # content after frontmatter
            "wiki_links": list[str],   # extracted [[link]] targets
        }
    """
    frontmatter, body = extract_frontmatter(content)
    tags = extract_tags(frontmatter, body)
    wiki_links = extract_wiki_links(content)
    return {
        "frontmatter": frontmatter,
        "tags": tags,
        "body": body,
        "wiki_links": wiki_links,
    }


def extract_frontmatter(content: str) -> tuple[dict, str]:
    """Split YAML frontmatter from body.

    Returns (frontmatter_dict, body_string).
    If no valid frontmatter is found, returns ({}, original_content).
    """
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return {}, content

    raw_yaml = match.group(1)
    body = content[match.end():]

    try:
        parsed = yaml.safe_load(raw_yaml)
    except yaml.YAMLError:
        # Malformed YAML (e.g. Templater syntax) — return empty dict
        return {}, content

    if not isinstance(parsed, dict):
        # YAML parsed to a scalar or list — not useful as frontmatter
        return {}, content

    return parsed, body


def extract_tags(frontmatter: dict, body: str) -> list[str]:
    """Merge tags from YAML frontmatter and inline #hashtags.

    Frontmatter tags can be:
    - A string: "meeting"
    - A list: ["meeting", "daily"]
    - A comma-separated string: "meeting, daily"

    All tags are lowercased and deduplicated, preserving order.
    """
    tags: list[str] = []

    # Tags from frontmatter
    fm_tags = frontmatter.get("tags", frontmatter.get("tag", []))
    if isinstance(fm_tags, str):
        # Could be comma-separated: "meeting, daily"
        for t in fm_tags.split(","):
            t = t.strip().lower()
            if t:
                tags.append(t)
    elif isinstance(fm_tags, list):
        for t in fm_tags:
            if isinstance(t, str):
                tags.append(t.strip().lower())

    # Inline hashtags from body
    for match in _INLINE_TAG_RE.finditer(body):
        tag = match.group(1).lower()
        tags.append(tag)

    # Deduplicate preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            unique.append(t)

    return unique


def extract_wiki_links(content: str) -> list[str]:
    """Extract all [[wiki-link]] targets from content.

    Handles both [[target]] and [[target|display text]] formats.
    Returns deduplicated list preserving first-occurrence order.
    """
    seen: set[str] = set()
    links: list[str] = []
    for match in _WIKI_LINK_RE.finditer(content):
        target = match.group(1).strip()
        if target and target not in seen:
            seen.add(target)
            links.append(target)
    return links
