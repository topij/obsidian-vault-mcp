FROM python:3.12-slim

# Pin uv to a specific version for reproducible builds.
COPY --from=ghcr.io/astral-sh/uv:0.9.28 /uv /bin/uv

WORKDIR /app

# Install dependencies first (cached layer)
COPY pyproject.toml uv.lock* README.md ./
RUN uv sync --frozen --no-dev

# Copy source
COPY obsidian_vault_mcp/ ./obsidian_vault_mcp/

# Non-root user. UID/GID default to 1000 but can be overridden at build time
# to match the vault owner on the host (e.g. Syncthing running as root → 0).
ARG APP_UID=1000
ARG APP_GID=1000
RUN groupadd -g ${APP_GID} appuser 2>/dev/null || true \
    && useradd -r -u ${APP_UID} -g ${APP_GID} -d /app -s /bin/false appuser 2>/dev/null || true \
    && chown -R ${APP_UID}:${APP_GID} /app
USER ${APP_UID}:${APP_GID}

# Vault directory is bind-mounted at runtime (/app/vault)

EXPOSE 8002

CMD ["uv", "run", "python", "-m", "obsidian_vault_mcp.server"]
