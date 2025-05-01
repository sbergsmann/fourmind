# ==========================
# STAGE 1: Dependencies
# ==========================
# Version from 0.6.14 onwards use 3.12.10 python version by default!
FROM ghcr.io/astral-sh/uv:0.6.13-python3.12-bookworm-slim AS builder


RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# - silence uv complaining about not being able to use hard links,
# - tell uv to byte-compile packages for faster application startups,
# - prevent uv from accidentally downloading isolated Python builds,
# - pick a Python (use `/usr/bin/python3.12` on uv 0.5.0 and later),
# - and finally declare `/app` as the target for `uv sync`.
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=python3.12 \
    UV_PROJECT_ENVIRONMENT=/app

# Synchronize DEPENDENCIES without the application itself.
# This layer is cached until uv.lock or pyproject.toml change, which are
# only temporarily mounted into the build container since we don't need
# them in the production one.
# You can create `/app` using `uv venv` in a separate `RUN`
# step to have it cached, but with uv it's so fast, it's not worth
# it, so we let `uv sync` create it for us automagically.
RUN --mount=type=cache,target=/root/.cache \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project

# Now install the rest from `/src`: The APPLICATION w/o dependencies.
# `/src` will NOT be copied into the runtime container.
# LEAVE THIS OUT if your application is NOT a proper Python package.
# COPY . /src
# WORKDIR /src
# RUN --mount=type=cache,target=/root/.cache \
#     uv sync --locked --no-dev --no-editable

# ==========================
# STAGE 2: Base Runtime
# ==========================

FROM python:3.12-slim-bookworm AS base

ENV PATH=/app/bin:$PATH

RUN groupadd --system app && useradd --system --home-dir /app --gid app --no-user-group app

STOPSIGNAL SIGINT

COPY --from=builder --chown=app:app /app /app

USER app

# ==========================
# STAGE 3: Fourmind
# ==========================
FROM base AS fourmind

# Copy application code (source files)
COPY --chown=app:app /src /app
WORKDIR /app
CMD ["python", "-m", "fourmind.bot.client"]