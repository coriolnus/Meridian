# Meridian — one image, two roles (cadence + read-only dashboard), selected by env in docker-compose.
#
# HER İKİ ROL DE AYNI KOMUTU KOŞAR (uvicorn); rolü ayıran şey `MERIDIAN_AUTOSTART_CYCLE`tir:
# 1 ise api süreç-içi `scheduler.start()` bağlar (24/7 kadans), değilse süreç salt-okuma panosudur.
# ESKİ CMD `python -m meridian.run` İDİ ve `run.worker()`ı çağırıyordu — 24/7 kadansın İKİNCİ bir
# uygulaması (C3, 2026-08-02: emekli edildi; gerekçe meridian/run.py docstring'inde). O yol bugün
# yüksek sesle reddeder, yani bu satır değişmeseydi konteyner hiç kalkmazdı.
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

# default = the api process; the CADENCE is in-process and switched on by MERIDIAN_AUTOSTART_CYCLE=1
# (docker-compose sets it on the `worker` service only). 127.0.0.1 çünkü kadans süreci dışarıdan
# çağrılmaz; panoyu yayınlayan servis kendi ayarını compose'da verir.
CMD ["uvicorn", "meridian.api:app", "--host", "127.0.0.1", "--port", "8080"]
