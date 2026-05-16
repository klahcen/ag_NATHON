# FastAPI backend — works with either Railway layout:
#   • Root Directory = backend   (build context = backend/)
#   • Root Directory = repo root (build context = ., Dockerfile path = backend/Dockerfile)

FROM python:3.12-slim AS src
WORKDIR /src
COPY . .
RUN set -eux; \
    if [ -f requirements.txt ]; then \
      APP=.; \
    elif [ -f backend/requirements.txt ]; then \
      APP=backend; \
    else \
      echo "ERROR: requirements.txt not found (expected at ./ or ./backend/)" >&2; \
      ls -la . >&2; \
      exit 1; \
    fi; \
    mkdir -p /build && cp -a "$APP"/. /build/

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

ARG PIP_CACHE_BUST=2026-05-16-railway

COPY --from=src /build/requirements.txt ./
RUN pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt \
 && pip install "uvicorn[standard]" fastapi \
 && python -c "import uvicorn, fastapi; print('uvicorn', uvicorn.__version__, 'fastapi', fastapi.__version__)"

COPY --from=src /build/ ./

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -sf "http://127.0.0.1:${PORT:-8000}/healthz" || exit 1

CMD ["sh", "-c", "exec python -m uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}"]
