# utils/dedup.py
import json
import os

from utils.paths import data_path


def load_seen_urls():
    path = data_path("seen_urls.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_seen_urls(urls):
    path = data_path("seen_urls.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(urls, f, indent=2)


def is_new(url, seen_urls):
    return url not in seen_urls
