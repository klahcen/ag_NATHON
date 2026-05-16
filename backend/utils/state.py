# utils/state.py
import json
import os
from datetime import datetime, timedelta

from utils.paths import data_path


def get_last_run():
    """Récupère la date de la dernière exécution du pipeline."""
    path = data_path("last_run.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return datetime.fromisoformat(data.get("last_run"))
            except Exception:
                pass
    return None


def update_last_run():
    """Met à jour le fichier d'état avec l'heure actuelle."""
    path = data_path("last_run.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"last_run": datetime.now().isoformat()}, f)


def is_within_freshness_window(event_date_str, config):
    """
    Vérifie si la date de l'événement respecte la règle (ex: passé de 14j max, futur de 180j max).
    """
    if not event_date_str:
        return False

    try:
        event_date = datetime.strptime(event_date_str, "%Y-%m-%d")
        now = datetime.now()

        past_limit = now - timedelta(days=config["freshness_window"]["past_days"])
        future_limit = now + timedelta(days=config["freshness_window"]["future_days"])

        return past_limit <= event_date <= future_limit
    except ValueError:
        return False
