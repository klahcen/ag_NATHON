# api.py — read/write microservice for curated events.
# Source of truth: data/*.json (written by main.py pipeline). Falls back to
# sample_events/published.json so a fresh deploy never returns an empty radar.

import requests
import json
import os

from datetime import datetime
from typing import List, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from utils.paths import get_data_dir, data_path as _data_path

load_dotenv()

_BACKEND_ROOT = os.path.dirname(os.path.abspath(__file__))
_SAMPLE = os.path.join(_BACKEND_ROOT, "sample_events", "published.json")

# Récupération sécurisée des variables
CALCOM_API_KEY = os.getenv("CALCOM_API_KEY")
CALCOM_USERNAME = os.getenv("CALCOM_USERNAME")
CALCOM_EVENT_SLUG = os.getenv("CALCOM_EVENT_SLUG")

app = FastAPI(title="InsureNow Curator API")

# CORS: relaxed by default; restrict via CURATOR_CORS_ORIGINS="https://foo,https://bar".
_origins_env = os.environ.get("CURATOR_CORS_ORIGINS", "*").strip()
_origins: List[str] = ["*"] if _origins_env in ("", "*") else [o.strip() for o in _origins_env.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_json(filepath: str):
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_json(data, filepath: str) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _dedup_by_id(events: list) -> list:
    seen: set = set()
    out = []
    for e in events:
        if not isinstance(e, dict):
            continue
        key = e.get("event_id") or e.get("url") or id(e)
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out


# ---------------------------------------------------------
# Health
# ---------------------------------------------------------
@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "data_dir": get_data_dir(),
        "data_dir_exists": os.path.isdir(get_data_dir()),
        "events_count": len(load_json(_data_path("events.json"))),
        "queue_count": len(load_json(_data_path("review_queue.json"))),
        "sample_present": os.path.exists(_SAMPLE),
    }


# ---------------------------------------------------------
# Reads
# ---------------------------------------------------------
@app.get("/api/events/queue")
def get_queue():
    return load_json(_data_path("review_queue.json"))


@app.get("/api/events/published")
def get_published():
    events_file = _data_path("events.json")
    
    # Si le fichier existe, on le renvoie (même s'il est vide)
    if os.path.exists(events_file):
        return load_json(events_file)
        
    # S'il n'existe pas, on renvoie simplement un tableau vide (fini les samples !)
    return []


@app.get("/api/events/rejected")
def get_rejected():
    return load_json(_data_path("not_events.json"))


# ==========================================
# CONFIGURATION CAL.COM
# ==========================================

@app.get("/api/calendar/slots")
def get_calendar_slots(start: str, end: str):
    url = f"https://api.cal.com/v2/slots?eventTypeSlug={CALCOM_EVENT_SLUG}&username={CALCOM_USERNAME}&start={start}&end={end}"
    
    headers = {
        "Authorization": f"Bearer {CALCOM_API_KEY}",
        "cal-api-version": "2024-09-04", # LA FAMEUSE DATE MAGIQUE DE LA DOCUMENTATION
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # En V2, les données sont encapsulées dans "data"
        slots_data = data.get("data", {})
        return {"slots": slots_data}
        
    except Exception as e:
        return {"error": str(e), "slots": {}}


# ---------------------------------------------------------
# Mutations (curator UI / human review)
# ---------------------------------------------------------
class EventAction(BaseModel):
    event_id: str
    action: str  # "publish" | "reject"
    updated_data: Optional[dict] = None


@app.post("/api/events/action")
def process_event(payload: EventAction):
    queue = load_json(_data_path("review_queue.json"))
    published = load_json(_data_path("events.json"))
    rejected = load_json(_data_path("not_events.json"))

    event = next((e for e in queue if e.get("event_id") == payload.event_id), None)
    if not event:
        raise HTTPException(status_code=404, detail="Événement introuvable")

    if payload.updated_data:
        event.update(payload.updated_data)

    queue = [e for e in queue if e.get("event_id") != payload.event_id]
    now_iso = datetime.now().isoformat()

    if payload.action == "publish":
        event["status"] = "published"
        event["last_verified_at"] = now_iso
        published.append(event)
        save_json(published, _data_path("events.json"))
    elif payload.action == "reject":
        rejected.append({
            "title": event.get("title"),
            "url": event.get("url"),
            "source": event.get("source"),
            "rejected_at": now_iso,
            "reason": "Rejeté manuellement par le Curator",
        })
        save_json(rejected, _data_path("not_events.json"))
    else:
        raise HTTPException(status_code=400, detail="action must be 'publish' or 'reject'")

    save_json(queue, _data_path("review_queue.json"))
    return {"status": "success", "message": f"Événement traité : {payload.action}"}


# Local dev: uvicorn api:app --reload --host 0.0.0.0 --port 8000
