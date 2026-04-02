# obsidian-vault-mcp — Plan

## What this is

Headless MCP server for direct Obsidian vault access (filesystem, no app needed).
Third knowledge store alongside voice-notes (port 8000) and Brain (port 8001).
Powers `/synthesize`, `/graduate`, `/drift`, and `/context` slash commands.

Built with FastMCP. Core modules (`vault.py`, `frontmatter.py`) have zero MCP deps and are reusable.

## Current state

Server runs locally via launchd (`com.topi.obsidian-vault-mcp`), SSE on port 8002.
Vault: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian-notes` (~1,930 files).

9 tools: `vault_list`, `vault_read`, `vault_write`, `vault_search`, `vault_search_by_tag`, `vault_recent`, `vault_move`, `vault_structure`, `vault_backlinks`.

## Done

- [x] Sprint 1: Core MCP server (frontmatter parsing, vault ops, 9 tools, tests)
- [x] LaunchAgent for local dev (`com.topi.obsidian-vault-mcp`, KeepAlive, port 8002)
- [x] `run-local.sh` convenience script
- [x] Directory rename: `obsidian-mcp` -> `obsidian-vault-mcp` (LaunchAgent updated 2026-03-31)
- [x] Sprint 2: Syncthing Mac <-> CT 104 (bidirectional, 2,293 files, <10s propagation)
- [x] Sprint 3: Deploy to CT 104 (Docker, Cloudflare tunnel `obsidian.topi.me`)
- [x] All three MCPs configured via tunnels in `~/.claude/settings.json`:
  - `voice-notes` → `https://notes.topi.me/sse`
  - `brain` → `https://brain.topi.me/sse`
  - `obsidian` → `https://obsidian.topi.me/sse`

## Next up

### Sprint 4: Integration

- [x] CLAUDE.md at vault root — already exists, comprehensive and accurate
- [x] Slash commands (`/context`, `/synthesize`, `/graduate`, `/drift`) — all reference obsidian MCP ops, will resolve at runtime
- [x] Vault cleanup — Phase A structural fixes + Phase B content mapping (2026-04-02)
  - Fixed folder numbering: 20-PROJECTS→30-PROJECTS, 30-SYNTHESIS→20-SYNTHESIS
  - Consolidated duplicate Readwise folders (Notes/Readwise→40-REFERENCE/Readwise, deleted 552 stale files)
  - Removed Trash/, empty folders, 8 junk/empty files
  - Moved 3 inbox items to 40-REFERENCE, OpenKitchen AI to 30-PROJECTS
  - Updated vault CLAUDE.md
  - MCP server connection: requires `type: "sse"` in config + `.mcp.json` at project root
- [ ] Vault cleanup Phase B2 — restructure subfolders within main-level folders (40-REFERENCE legacy, 10-NOTES organization)

## Architecture notes

- No database — ~1,930 files scans in <1s, avoids index/filesystem sync issues
- Atomic writes (temp file + `os.replace()`) — safe for Syncthing
- Excluded dirs: `.obsidian/`, `.git/`, `.smart-env/`, `Trash/`, `assets/`, `node_modules/`
- iCloud vault path — macOS rarely evicts files this small (167MB)
- Docker on CT 104: `python:3.12-slim` + uv, cloudflared with `--protocol http2` (LXC requirement)
- Syncthing: Mac (homebrew, launchd) <-> CT 104 (apt, systemd@root), folder ID `obsidian-vault`
- Project deployed to `/root/obsidian-vault-mcp` on CT 104
- Note: `notes.topi.me` has Cloudflare Access enabled — may need service token for SSE
