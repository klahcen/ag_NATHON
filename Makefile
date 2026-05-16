# InsureNow Event Curator — local dev & deploy helpers
# Usage: make help

.PHONY: help install install-backend install-frontend \
        dev dev-api dev-web api web pipeline \
        build build-frontend docker-frontend docker-up health seed clean railway-hint

ROOT     := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
BACKEND  := $(ROOT)backend
FRONTEND := $(ROOT)frontend
VENV     := $(BACKEND)/.venv
PY       := $(VENV)/bin/python
PIP      := $(VENV)/bin/pip
API_HOST ?= 0.0.0.0
API_PORT ?= 8000
WEB_PORT ?= 3001

help:
	@echo "InsureNow Event Curator"
	@echo ""
	@echo "  make install          Install backend + frontend dependencies"
	@echo "  make dev              Run API + frontend (two terminals: make dev-api & make dev-web)"
	@echo "  make dev-api          Start FastAPI on http://localhost:$(API_PORT)"
	@echo "  make dev-web          Start Next.js on http://localhost:$(WEB_PORT)"
	@echo "  make pipeline         Run scraper (needs ANTHROPIC_API_KEY in backend/.env)"
	@echo "  make health           Curl API healthz"
	@echo "  make seed             Copy sample events into data/review_queue.json"
	@echo "  make build-frontend   Production build for Next.js"
	@echo "  make docker-frontend  Run Next.js in Docker (see docker-compose.yml)"
	@echo "  make docker-up        Run frontend + API containers"
	@echo "  make railway-hint     Print Railway deploy settings (3 services)"
	@echo "  make clean            Remove caches (not .venv)"

# --- Setup ---

install: install-backend install-frontend

install-backend:
	@if [ ! -x $(PIP) ]; then rm -rf $(VENV); python3 -m venv $(VENV); fi
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r $(BACKEND)/requirements.txt
	@echo "Backend ready. Activate: source backend/.venv/bin/activate"

install-frontend:
	cd $(FRONTEND) && npm install
	@echo "Frontend ready."

# --- Run ---

dev-api api:
	cd $(BACKEND) && $(PY) -m uvicorn api:app --reload --host $(API_HOST) --port $(API_PORT)

dev-web web:
	cd $(FRONTEND) && npm run dev

dev:
	@echo "Run in two terminals:"
	@echo "  make dev-api"
	@echo "  make dev-web"
	@echo "Then open http://localhost:$(WEB_PORT)"

pipeline:
	cd $(BACKEND) && $(PY) main.py

# --- Utils ---

health:
	@curl -sf http://localhost:$(API_PORT)/healthz | python3 -m json.tool || \
		(echo "API not running. Start with: make dev-api" && exit 1)

seed:
	cd $(BACKEND) && $(PY) -c "\
import json; \
from utils.paths import data_path, get_data_dir; \
sample = json.load(open('sample_events/published.json', encoding='utf-8')); \
queue = [{**e, 'status': 'queued_for_review'} for e in sample]; \
open(data_path('review_queue.json'), 'w', encoding='utf-8').write(json.dumps(queue, indent=2, ensure_ascii=False)); \
print('Seeded', len(queue), 'events ->', get_data_dir())"

build-frontend:
	cd $(FRONTEND) && npm run build

docker-frontend:
	@echo "Frontend container → http://localhost:3000  (API: make dev-api → :8000)"
	docker-compose up --build --force-recreate frontend

docker-up:
	@echo "Frontend → http://localhost:3000  |  API → http://localhost:8000"
	docker-compose up --build --force-recreate

clean:
	rm -rf $(FRONTEND)/.next $(FRONTEND)/out
	find $(BACKEND) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

railway-hint:
	@echo "Railway — 3 services, same GitHub repo (ag_NATHON):"
	@echo ""
	@echo "  1) FRONTEND (Docker container — Next.js)"
	@echo "     Root Directory:  frontend          ← required"
	@echo "     Builder:         Dockerfile        (frontend/railway.toml)"
	@echo "     NOT Railpack at repo root"
	@echo "     Variable:        NEXT_PUBLIC_API_URL=https://<backend>.up.railway.app"
	@echo ""
	@echo "  2) BACKEND (API — FastAPI)  — service name can be ag_NATHON or backend"
	@echo "     Root Directory:  backend           (or repo root + backend/Dockerfile)"
	@echo "     Builder:         Dockerfile        (backend/railway.toml)"
	@echo "     Health:          /healthz"
	@echo "     Do NOT use frontend/Dockerfile for this service"
	@echo ""
	@echo "  3) PIPELINE (scraper — main.py, optional cron)"
	@echo "     Root Directory:  backend"
	@echo "     Builder:         Dockerfile"
	@echo "     Start command:   python main.py"
	@echo "     Cron:            0 */6 * * *  (or use backend/railway.pipeline.toml)"
	@echo "     Variables:       ANTHROPIC_API_KEY, etc."
	@echo ""
	@echo "If build logs list Makefile + frontend/ at repo root, Root Directory is wrong."
