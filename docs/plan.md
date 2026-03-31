# obsidian-vault-mcp — Plan

## What this is

Headless MCP server for direct Obsidian vault access (filesystem, no app needed).
Third knowledge store alongside voice-notes (port 8000) and Brain (port 8001).
Powers `/synthesize`, `/graduate`, `/drift`, and `/context` slash commands.

Built with FastMCP. Core modules (`vault.py`, `frontmatter.py`) have zero MCP deps and are reusable.

## Current state

Server runs locally via launchd (`com.topi.obsidian-vault-mcp`), SSE on port 8002.
Vault: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian-notes` (1,380 files).

9 tools: `vault_list`, `vault_read`, `vault_write`, `vault_search`, `vault_search_by_tag`, `vault_recent`, `vault_move`, `vault_structure`, `vault_backlinks`.

## Done

- [x] Sprint 1: Core MCP server (frontmatter parsing, vault ops, 9 tools, tests)
- [x] LaunchAgent for local dev (`com.topi.obsidian-vault-mcp`, KeepAlive, port 8002)
- [x] `run-local.sh` convenience script
- [x] Directory rename: `obsidian-mcp` -> `obsidian-vault-mcp` (LaunchAgent updated 2026-03-31)

## Next up

### Sprint 2: Syncthing (Mac <-> NUC)

Sync vault to CT 104 so headless server can access it remotely.

- [ ] Install & configure Syncthing on Mac
- [ ] Install & configure Syncthing on CT 104 (192.168.68.104)
- [ ] Pair devices, share vault folder -> `/root/obsidian-vault`
- [ ] Verify bidirectional sync

### Sprint 3: Deploy to CT 104

- [ ] rsync project to CT 104
- [ ] `docker compose up -d --build`, verify health endpoint
- [ ] Firewall rule: IN ACCEPT 192.168.68.0/24 TCP 8002
- [ ] Cloudflare tunnel (`obsidian.topi.me` -> `http://mcp-server:8002`)
- [ ] Connect Claude Code: `claude mcp add --transport sse obsidian http://192.168.68.104:8002/sse`

### Sprint 4: Integration

- [ ] Create CLAUDE.md at vault root (data sources, interests, vault structure, how-to-help)
- [ ] Verify `/context`, `/synthesize`, `/graduate`, `/drift` slash commands use this MCP
- [ ] Vault cleanup — Claude-assisted review and reorganization

## Architecture notes

- No database — 1,380 files scans in <1s, avoids index/filesystem sync issues
- Atomic writes (temp file + `os.replace()`) — safe for Syncthing
- Excluded dirs: `.obsidian/`, `.git/`, `.smart-env/`, `Trash/`, `assets/`, `node_modules/`
- iCloud vault path — macOS rarely evicts files this small (167MB)
- Docker on CT 104: `python:3.12-slim` + uv, cloudflared with `--protocol http2` (LXC requirement)
