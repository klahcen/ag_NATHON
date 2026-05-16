# Curator microservice (FastAPI, read-only) — exposes /api/events/* over HTTP.
# Heavy scraping work (Playwright + Anthropic) runs separately as `make curator-pipeline`
# (host venv) or `docker compose run curator-pipeline`. The API container itself does
# NOT need chromium and stays small and fast to boot.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

# Minimal system deps. lxml/feedparser/requests/etc. ship wheels for slim, so we don't
# need build-essential here. If a future dep needs gcc, switch to python:3.12 (non-slim).
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

# Bump the cache key whenever requirements need a forced reinstall (Railway/CI).
ARG PIP_CACHE_BUST=2026-05-10-fix-uvicorn

# Install Python deps. Then explicitly add fastapi+uvicorn (belt-and-braces; some PaaS
# build caches were observed serving the previous layer where uvicorn was somehow
# missing → "No module named uvicorn" at runtime). Finally, fail the build if either
# package can't be imported, so we never deploy a broken image.
COPY requirements.txt ./
RUN pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt \
 && pip install "uvicorn[standard]" fastapi \
 && python -c "import uvicorn, fastapi; print('uvicorn', uvicorn.__version__, 'fastapi', fastapi.__version__)"

# Copy application code (api.py + sources/utils/sample_events). data/ is a runtime volume.
COPY . ./

EXPOSE 8000

# Railway and most PaaS providers inject $PORT at runtime; default to 8000 for compose.
# Invoke through `python -m uvicorn` so we don't depend on the uvicorn console script
# being on PATH (some PaaS shells strip /usr/local/bin from the CMD environment, which
# manifests as "sh: 1: uvicorn: not found" at runtime even though pip installed fine).
#
# Defensive cd: when Railway's build context is the repo root (instead of
# event_curator/backend), our files end up under /app/event_curator/backend/. We try
# both layouts so this image is portable. If neither has api.py, we print the layout
# of /app to logs so the failure mode is obvious.
#
# `exec` makes Python PID 1 → it receives SIGTERM and shuts down cleanly.
CMD ["sh", "-c", "\
  if [ -f /app/api.py ]; then APP_DIR=/app; \
  elif [ -f /app/event_curator/backend/api.py ]; then APP_DIR=/app/event_curator/backend; \
  else echo 'ERROR: api.py not found in /app or /app/event_curator/backend' >&2; \
       echo '--- /app contents ---' >&2; ls -la /app >&2; \
       exit 1; \
  fi; \
  cd \"$APP_DIR\" && \
  echo \"Starting curator from $APP_DIR on port ${PORT:-8000}\" && \
  exec python -m uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}\
"]
