# syntax=docker/dockerfile:1

# ============================================================================
# Multi-stage build. Debian slim (not Alpine) so mysqlclient/pillow/reportlab
# build against glibc with prebuilt system libs instead of a musl toolchain.
# Dependencies are resolved by uv from the committed uv.lock for reproducible,
# hash-verified installs.
# ============================================================================

# ---------- Stage 1: builder (resolves deps into a venv via uv) -------------
FROM python:3.12-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:0.11.25 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv

# Build-time only: mysqlclient has no manylinux wheel and compiles from
# source against libmysqlclient/libmariadb headers.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        pkg-config \
        default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev


# ---------- Stage 2: runtime (small final image) -----------------------------
FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=America/Belem \
    PATH="/opt/venv/bin:$PATH"

# Runtime-only libs:
# - libmariadb3: shared lib mysqlclient links against (the runtime half of
#   default-libmysqlclient-dev installed in the builder stage)
# - tzdata: timezone data for America/Belem
RUN apt-get update && apt-get install -y --no-install-recommends \
        libmariadb3 \
        tzdata \
    && ln -fs /usr/share/zoneinfo/America/Belem /etc/localtime \
    && echo "America/Belem" > /etc/timezone \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 app && useradd --uid 1000 --gid app --home-dir /app --no-create-home app

# Bring in the fully-resolved virtualenv from the builder stage.
COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

COPY --chown=app:app . .

# WORKDIR created /app as root before the COPY above set ownership on its
# contents; collectstatic/sqlite/media writes at runtime need /app itself
# (and the not-yet-existing staticfiles/media dirs) owned by the app user.
RUN mkdir -p /app/staticfiles /app/media && chown app:app /app /app/staticfiles /app/media

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import socket; s = socket.create_connection(('127.0.0.1', 8000), 5); s.close()" || exit 1

# Traefik (managed by Dokploy) reverse-proxies to this port directly —
# no in-image nginx/static server needed.
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["gunicorn", "-c", "./configs/gunicorn/conf.py", "gestao_estoque.wsgi"]
