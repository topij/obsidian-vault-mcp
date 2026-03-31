FROM python:3.12-slim

# Pin uv to a specific version for reproducible builds.
COPY --from=ghcr.io/astral-sh/uv:0.9.28 /uv /bin/uv

WORKDIR /app

# Install dependencies first (cached layer)
COPY pyproject.toml uv.lock* README.md ./
RUN uv sync --frozen --no-dev

# Copy source
COPY obsidian_vault_mcp/ ./obsidian_vault_mcp/

# Vault directory is bind-mounted at runtime (/app/vault)

EXPOSE 8002

CMD ["uv", "run", "python", "-m", "obsidian_vault_mcp.server"]
