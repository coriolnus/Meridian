# Meridian — one image, two roles (worker + dashboard), selected by command in docker-compose.
FROM python:3.12-slim

# uv for fast, reproducible installs
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=America/New_York

WORKDIR /opt/meridian

# deps first for layer caching
COPY pyproject.toml ./
RUN uv pip install --system \
    fastapi uvicorn "pandas>=2.1" "numpy>=1.26" pyyaml httpx aiofiles \
    pandas-market-calendars rich jinja2 google-cloud-secret-manager

# app + skills + immutable config
COPY meridian ./meridian
COPY skills ./skills
COPY state/goal.yaml state/bounds.yaml ./state/
COPY state/skills_registry.json ./state/

# non-root
RUN useradd -m meridian && chown -R meridian:meridian /opt/meridian
USER meridian

# default = the 24/7 worker; the dashboard service overrides this command
CMD ["python", "-m", "meridian.run"]
