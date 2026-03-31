"""Tests for vault filesystem operations."""

from pathlib import Path

import pytest

from obsidian_vault_mcp.vault import (
    count_files,
    get_backlinks,
    get_structure,
    list_files,
    move_note,
    read_note,
    recent_notes,
    search_by_tag,
    search_notes,
    write_note,
)


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    """Create a sample vault directory structure for testing."""
    # Create vault structure
    (tmp_path / "00-INBOX").mkdir()
    (tmp_path / "10-NOTES").mkdir()
    (tmp_path / "10-NOTES" / "daily-notes").mkdir()
    (tmp_path / "20-PROJECTS").mkdir()
    (tmp_path / "30-SYNTHESIS").mkdir()
    (tmp_path / "40-REFERENCE").mkdir()
    (tmp_path / ".obsidian").mkdir()
    (tmp_path / ".git").mkdir()
    (tmp_path / "assets").mkdir()

    # Create sample notes
    (tmp_path / "00-INBOX" / "quick-note.md").write_text(
        "# Quick Note\nJust a quick idea about #ai\n"
    )

    (tmp_path / "10-NOTES" / "transformers.md").write_text(
        "---\ntitle: Transformers\ntags: [ai, deep-learning]\n---\n"
        "#machine-learning\n\nTransformers are a type of neural network.\n"
        "See also [[attention mechanism]] and [[BERT]].\n"
    )

    (tmp_path / "10-NOTES" / "attention mechanism.md").write_text(
        "---\ntitle: Attention Mechanism\ntags: ai\n---\n"
        "Core building block of [[transformers]].\n"
    )

    (tmp_path / "10-NOTES" / "daily-notes" / "2025-06-10.md").write_text(
        "<< [[2025-06-09]] | [[2025-06-11]] >>\n\nToday's notes about #work\n"
    )

    (tmp_path / "40-REFERENCE" / "article.md").write_text(
        "---\ntitle: Some Article\ntags: [reading]\n---\nHighlights from the article.\n"
    )

    # A file in excluded directory (should be ignored)
    (tmp_path / ".obsidian" / "config.md").write_text("config file\n")

    return tmp_path


class TestListFiles:
    def test_list_all(self, vault: Path):
        results = list_files(vault)
        paths = [r["path"] for r in results]
        assert "10-NOTES/transformers.md" in paths
        assert "00-INBOX/quick-note.md" in paths
        # Excluded dirs should not appear
        assert ".obsidian/config.md" not in paths

    def test_list_subdirectory(self, vault: Path):
        results = list_files(vault, path="10-NOTES")
        paths = [r["path"] for r in results]
        assert "10-NOTES/transformers.md" in paths
        assert "00-INBOX/quick-note.md" not in paths

    def test_list_non_recursive(self, vault: Path):
        results = list_files(vault, path="10-NOTES", recursive=False)
        paths = [r["path"] for r in results]
        assert "10-NOTES/transformers.md" in paths
        # Should not include files in subdirectories
        assert "10-NOTES/daily-notes/2025-06-10.md" not in paths

    def test_list_with_limit(self, vault: Path):
        results = list_files(vault, limit=2)
        assert len(results) == 2

    def test_list_invalid_directory(self, vault: Path):
        with pytest.raises(ValueError):
            list_files(vault, path="nonexistent")

    def test_has_size_and_modified(self, vault: Path):
        results = list_files(vault, path="10-NOTES", limit=1)
        assert "size" in results[0]
        assert "modified" in results[0]
        assert results[0]["size"] > 0


class TestReadNote:
    def test_read_with_frontmatter(self, vault: Path):
        result = read_note(vault, "10-NOTES/transformers.md")
        assert result["frontmatter"]["title"] == "Transformers"
        assert "ai" in result["tags"]
        assert "deep-learning" in result["tags"]
        assert "machine-learning" in result["tags"]
        assert "attention mechanism" in result["wiki_links"]
        assert "BERT" in result["wiki_links"]

    def test_read_without_frontmatter(self, vault: Path):
        result = read_note(vault, "00-INBOX/quick-note.md")
        assert result["frontmatter"] == {}
        assert "ai" in result["tags"]

    def test_read_nonexistent(self, vault: Path):
        with pytest.raises(FileNotFoundError):
            read_note(vault, "nonexistent.md")

    def test_path_traversal_blocked(self, vault: Path):
        with pytest.raises(ValueError):
            read_note(vault, "../../etc/passwd")


class TestWriteNote:
    def test_create_new(self, vault: Path):
        result = write_note(vault, "30-SYNTHESIS/test.md", "# Test\nContent here\n")
        assert result["created"] is True
        assert result["size"] > 0
        assert (vault / "30-SYNTHESIS" / "test.md").read_text() == "# Test\nContent here\n"

    def test_create_with_new_directory(self, vault: Path):
        result = write_note(vault, "30-SYNTHESIS/subtopic/deep.md", "# Deep\n")
        assert result["created"] is True
        assert (vault / "30-SYNTHESIS" / "subtopic" / "deep.md").exists()

    def test_refuse_overwrite_by_default(self, vault: Path):
        with pytest.raises(FileExistsError):
            write_note(vault, "10-NOTES/transformers.md", "overwrite!")

    def test_allow_overwrite(self, vault: Path):
        result = write_note(vault, "10-NOTES/transformers.md", "new content", allow_overwrite=True)
        assert result["created"] is False
        assert (vault / "10-NOTES" / "transformers.md").read_text() == "new content"

    def test_path_traversal_blocked(self, vault: Path):
        with pytest.raises(ValueError):
            write_note(vault, "../../etc/evil.md", "bad stuff")


class TestSearchNotes:
    def test_basic_search(self, vault: Path):
        results = search_notes(vault, "neural network")
        assert len(results) == 1
        assert results[0]["path"] == "10-NOTES/transformers.md"
        assert results[0]["match_count"] >= 1
        assert any("neural network" in m["text"].lower() for m in results[0]["matches"])

    def test_case_insensitive(self, vault: Path):
        results = search_notes(vault, "TRANSFORMERS")
        assert len(results) >= 1

    def test_search_in_subdirectory(self, vault: Path):
        results = search_notes(vault, "notes", path="10-NOTES/daily-notes")
        assert all(r["path"].startswith("10-NOTES/daily-notes") for r in results)

    def test_search_no_results(self, vault: Path):
        results = search_notes(vault, "xyznonexistent123")
        assert results == []

    def test_empty_query_raises(self, vault: Path):
        with pytest.raises(ValueError):
            search_notes(vault, "")


class TestSearchByTag:
    def test_match_all(self, vault: Path):
        results = search_by_tag(vault, ["ai", "deep-learning"])
        paths = [r["path"] for r in results]
        assert "10-NOTES/transformers.md" in paths
        # attention mechanism has ai but not deep-learning
        assert "10-NOTES/attention mechanism.md" not in paths

    def test_match_any(self, vault: Path):
        results = search_by_tag(vault, ["ai", "reading"], match_all=False)
        paths = [r["path"] for r in results]
        assert "10-NOTES/transformers.md" in paths
        assert "40-REFERENCE/article.md" in paths

    def test_inline_tags(self, vault: Path):
        results = search_by_tag(vault, ["work"], match_all=True)
        paths = [r["path"] for r in results]
        assert "10-NOTES/daily-notes/2025-06-10.md" in paths

    def test_empty_tags_raises(self, vault: Path):
        with pytest.raises(ValueError):
            search_by_tag(vault, [])


class TestRecentNotes:
    def test_returns_recent(self, vault: Path):
        # All files were just created, so they should all be "recent"
        results = recent_notes(vault, days=1)
        assert len(results) > 0
        # Verify sorted by modified descending
        times = [r["modified"] for r in results]
        assert times == sorted(times, reverse=True)

    def test_limit(self, vault: Path):
        results = recent_notes(vault, days=1, limit=2)
        assert len(results) == 2


class TestMoveNote:
    def test_move_to_new_directory(self, vault: Path):
        result = move_note(vault, "00-INBOX/quick-note.md", "10-NOTES/quick-note.md")
        assert result["destination"] == "10-NOTES/quick-note.md"
        assert not (vault / "00-INBOX" / "quick-note.md").exists()
        assert (vault / "10-NOTES" / "quick-note.md").exists()

    def test_rename(self, vault: Path):
        result = move_note(vault, "00-INBOX/quick-note.md", "00-INBOX/renamed.md")
        assert result["destination"] == "00-INBOX/renamed.md"

    def test_move_nonexistent(self, vault: Path):
        with pytest.raises(FileNotFoundError):
            move_note(vault, "nonexistent.md", "somewhere.md")

    def test_move_to_existing(self, vault: Path):
        with pytest.raises(FileExistsError):
            move_note(vault, "00-INBOX/quick-note.md", "10-NOTES/transformers.md")


class TestGetStructure:
    def test_structure(self, vault: Path):
        result = get_structure(vault)
        assert result["total_files"] == 5  # 5 .md files in non-excluded dirs
        assert "10-NOTES" in result["folders"]
        assert result["folders"]["10-NOTES"]["files"] >= 1


class TestGetBacklinks:
    def test_find_backlinks(self, vault: Path):
        results = get_backlinks(vault, "transformers")
        paths = [r["path"] for r in results]
        assert "10-NOTES/attention mechanism.md" in paths

    def test_find_backlinks_case_insensitive(self, vault: Path):
        results = get_backlinks(vault, "BERT")
        paths = [r["path"] for r in results]
        assert "10-NOTES/transformers.md" in paths

    def test_no_self_links(self, vault: Path):
        results = get_backlinks(vault, "transformers")
        paths = [r["path"] for r in results]
        assert "10-NOTES/transformers.md" not in paths

    def test_no_backlinks(self, vault: Path):
        results = get_backlinks(vault, "quick-note")
        assert results == []


class TestCountFiles:
    def test_count(self, vault: Path):
        assert count_files(vault) == 5
