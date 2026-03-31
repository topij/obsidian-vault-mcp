"""Tests for frontmatter parsing."""

from obsidian_vault_mcp.frontmatter import (
    extract_frontmatter,
    extract_tags,
    extract_wiki_links,
    parse_note,
)


class TestExtractFrontmatter:
    def test_basic_frontmatter(self):
        content = "---\ntitle: Hello\ntags: [meeting]\n---\nBody text"
        fm, body = extract_frontmatter(content)
        assert fm == {"title": "Hello", "tags": ["meeting"]}
        assert body == "Body text"

    def test_no_frontmatter(self):
        content = "Just some text\nwith no frontmatter"
        fm, body = extract_frontmatter(content)
        assert fm == {}
        assert body == content

    def test_empty_frontmatter(self):
        content = "---\n---\nBody"
        fm, body = extract_frontmatter(content)
        # yaml.safe_load("") returns None, which is not a dict
        assert fm == {}

    def test_malformed_yaml(self):
        content = "---\n<% tp.file.title %>\n---\nBody"
        fm, body = extract_frontmatter(content)
        assert fm == {}
        assert body == content

    def test_frontmatter_not_at_start(self):
        content = "Some text\n---\ntitle: Hello\n---\nBody"
        fm, body = extract_frontmatter(content)
        assert fm == {}
        assert body == content

    def test_scalar_yaml(self):
        content = "---\njust a string\n---\nBody"
        fm, body = extract_frontmatter(content)
        assert fm == {}


class TestExtractTags:
    def test_yaml_list_tags(self):
        fm = {"tags": ["meeting", "daily"]}
        tags = extract_tags(fm, "")
        assert tags == ["meeting", "daily"]

    def test_yaml_string_tag(self):
        fm = {"tags": "meeting"}
        tags = extract_tags(fm, "")
        assert tags == ["meeting"]

    def test_yaml_comma_separated(self):
        fm = {"tags": "meeting, daily, review"}
        tags = extract_tags(fm, "")
        assert tags == ["meeting", "daily", "review"]

    def test_inline_hashtags(self):
        body = "#education #future-of-work\n\nSome text here"
        tags = extract_tags({}, body)
        assert "education" in tags
        assert "future-of-work" in tags

    def test_merged_and_deduplicated(self):
        fm = {"tags": ["meeting"]}
        body = "Some #meeting notes with #ai tag"
        tags = extract_tags(fm, body)
        assert tags == ["meeting", "ai"]

    def test_tag_key_fallback(self):
        fm = {"tag": "solo"}
        tags = extract_tags(fm, "")
        assert tags == ["solo"]

    def test_no_tags(self):
        tags = extract_tags({}, "Plain text with no tags")
        assert tags == []

    def test_anchor_link_not_matched(self):
        body = "See [heading](#anchor-link) for details"
        tags = extract_tags({}, body)
        assert "anchor-link" not in tags

    def test_tags_lowercased(self):
        fm = {"tags": ["Meeting", "AI"]}
        body = "#DeepLearning"
        tags = extract_tags(fm, body)
        assert tags == ["meeting", "ai", "deeplearning"]

    def test_finnish_tags(self):
        body = "#koulutus #tekoäly"
        tags = extract_tags({}, body)
        assert "koulutus" in tags
        assert "tekoäly" in tags

    def test_nested_tag_with_slash(self):
        body = "#status/done #project/ai-tool"
        tags = extract_tags({}, body)
        assert "status/done" in tags
        assert "project/ai-tool" in tags


class TestExtractWikiLinks:
    def test_basic_link(self):
        links = extract_wiki_links("See [[some note]] for details")
        assert links == ["some note"]

    def test_link_with_display_text(self):
        links = extract_wiki_links("See [[2025-06-09|Yesterday]] for context")
        assert links == ["2025-06-09"]

    def test_multiple_links(self):
        content = "<< [[2025-06-09]] | [[2025-06-11]] >>"
        links = extract_wiki_links(content)
        assert links == ["2025-06-09", "2025-06-11"]

    def test_deduplicated(self):
        content = "[[note]] and [[note]] again"
        links = extract_wiki_links(content)
        assert links == ["note"]

    def test_no_links(self):
        links = extract_wiki_links("Plain text, no links")
        assert links == []


class TestParseNote:
    def test_full_note(self):
        content = """---
title: Test Note
tags: [meeting, daily]
---
#ai #research

Some body text with a [[wiki-link]].
"""
        result = parse_note(content)
        assert result["frontmatter"]["title"] == "Test Note"
        assert "meeting" in result["tags"]
        assert "daily" in result["tags"]
        assert "ai" in result["tags"]
        assert "research" in result["tags"]
        assert "wiki-link" in result["wiki_links"]
        assert "Some body text" in result["body"]

    def test_no_frontmatter(self):
        content = "Just text with a [[link]]"
        result = parse_note(content)
        assert result["frontmatter"] == {}
        assert result["wiki_links"] == ["link"]

    def test_empty_content(self):
        result = parse_note("")
        assert result["frontmatter"] == {}
        assert result["tags"] == []
        assert result["body"] == ""
        assert result["wiki_links"] == []
