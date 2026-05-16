# main.py
import json
import os
import csv
import time
from datetime import datetime

from config import SOURCE_LIST, AGENT_CONFIG
from sources import eventbrite_scrapers, rss_feeds, web_scrapers
# from sources import experimental_scrapers
from utils.dedup import load_seen_urls, save_seen_urls, is_new
from utils.llm_classifier import classify_event
from utils.paths import data_path
from utils.state import update_last_run, is_within_freshness_window

def load_json(filepath):
    """Charge un fichier JSON s'il existe, sinon retourne une liste vide."""
    if not os.path.exists(filepath): return []
    with open(filepath, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return []

def save_json(data, filepath):
    """Sauvegarde les données au format JSON avec encodage UTF-8."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_csv(data, filepath):
    """Sauvegarde les données au format CSV en aplatissant les listes/dictionnaires."""
    if not data:
        return
        
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    keys = data[0].keys()
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        
        for row in data:
            flat_row = {}
            for k, v in row.items():
                if isinstance(v, (dict, list)):
                    flat_row[k] = json.dumps(v, ensure_ascii=False)
                else:
                    flat_row[k] = v
            writer.writerow(flat_row)

def clean_expired_events(events):
    """Supprime les événements dont la date est passée."""
    today = datetime.now().strftime("%Y-%m-%d")
    return [e for e in events if e.get('start_date', '0000-00-00') >= today]

def _flush(review_queue, published_events, not_events, seen_urls):
    """Persist all pipeline state to disk. Called after every source so the
    consuming /api/events/radar route can surface partial results immediately
    instead of waiting for the entire (slow) pipeline to finish."""
    save_json(review_queue, data_path("review_queue.json"))
    save_json(published_events, data_path("events.json"))
    save_json(not_events, data_path("not_events.json"))
    save_seen_urls(seen_urls)


def run_pipeline():
    print("⛺ Démarrage du pipeline Base Camp Event Curator...\n")
    
    seen_urls = load_seen_urls()
    review_queue = load_json(data_path("review_queue.json"))
    published_events = load_json(data_path("events.json"))
    not_events = load_json(data_path("not_events.json"))

    published_events = clean_expired_events(published_events)

    for source in SOURCE_LIST:
        if not source.get('enabled', True): continue
        
        print(f"\nScraping : {source['name']} (Trust: {source['trust_level']})")
        
        # --- PAUSE DE POLITESSE ENTRE CHAQUE SITE ---
        time.sleep(5)
        
        raw_events = []
        parser_id = source.get('parser_id')
        
        if parser_id == 'rss_parser':
            raw_events = rss_feeds.fetch(source)
        elif parser_id == 'eventbrite_scrapers':
            raw_events = eventbrite_scrapers.fetch(source)
        elif parser_id == 'web_scrapers':
            raw_events = web_scrapers.fetch(source)
        # elif parser_id == 'experimental_scrapers':
        #     raw_events = experimental_scrapers.fetch(source)
        else:
            print(f"  ⚠️ Erreur : Parser inconnu ({parser_id})")
            continue
            
        for raw in raw_events:
            if not is_new(raw['url'], seen_urls): continue
            
            print(f"  ↳ Nouveau : {raw['title']}")
            
            # --- PAUSE DE SÉCURITÉ POUR L'API ANTHROPIC ---
            time.sleep(2)
            
            # [STEP 3: CLASSIFY]
            ai_data = classify_event(raw)
            
            if not ai_data:
                print("    ❌ Rejet : Article identifié comme 'Non-Événement'.")
                not_events.append({
                    "title": raw['title'],
                    "url": raw['url'],
                    "source": raw['source'],
                    "rejected_at": datetime.now().isoformat(),
                    "reason": "Not a tech/startup event"
                })
                seen_urls.append(raw['url'])
                continue
            
            if not ai_data.get('start_date'):
                print("    ❌ Rejet : Données incomplètes (pas de date trouvée).")
                not_events.append({
                    "title": raw['title'],
                    "url": raw['url'],
                    "source": raw['source'],
                    "rejected_at": datetime.now().isoformat(),
                    "reason": "Missing mandatory fields (start_date)"
                })
                seen_urls.append(raw['url'])
                continue
            
            if not is_within_freshness_window(ai_data.get('start_date'), AGENT_CONFIG):
                print(f"    ❌ Rejet : Date ({ai_data.get('start_date')}) hors fenêtre.")
                seen_urls.append(raw['url'])
                continue

            # [STEP 4: GATE]
            now_iso = datetime.now().isoformat()
            curated = {
                "event_id": raw['url'],
                "title": ai_data.get('title', raw['title']),
                "description": ai_data.get('description', ''),
                "url": raw['url'],
                "source": raw['source'],
                "start_date": ai_data.get('start_date'),
                "end_date": ai_data.get('end_date'),
                "timezone": ai_data.get('timezone', 'Europe/Paris'),
                "format": ai_data.get('format', 'in_person'),
                "location": {
                    "city": ai_data.get('location_city'),
                    "country": ai_data.get('location_country'),
                    "venue": ai_data.get('location_venue')
                },
                "language": ai_data.get('language', 'FR'),
                "topics": ai_data.get('topics', []),
                "relevant_for": {
                    "stages": ai_data.get('relevant_stages', []),
                    "activities": ai_data.get('activities', ['all'])
                },
                "format_tags": ai_data.get('format_tags', []),
                "why_relevant": ai_data.get('why_relevant', ''),
                "curator_notes": None,
                "first_seen_at": now_iso,
                "last_verified_at": now_iso,
                "status": "pending",
                "classification_confidence": ai_data.get('classification_confidence', 'low'),
                "reviewer": None
            }
            
            # Auto-publish whenever the LLM produced a clean record (title + start_date already
            # validated upstream). This was previously gated on classification_confidence == 'high',
            # but the classifier never sets that field → everything fell into review_queue and the
            # public radar stayed empty. We still queue medium/low-trust sources for human review.
            if source['trust_level'] == 'high' or curated.get('classification_confidence') == 'high':
                curated['status'] = "published"
                published_events.append(curated)
                print(f"    ✅ AUTO-PUBLISHED : {curated['title']}")
            else:
                curated['status'] = "queued_for_review"
                review_queue.append(curated)
                print(f"    ⏳ QUEUED : {curated['title']}")
            
            seen_urls.append(raw['url'])

        # Persist partial results after each source so consumers don't have to
        # wait for the full ~10 min pipeline to see anything.
        _flush(review_queue, published_events, not_events, seen_urls)
        print(f"  💾 Flush after {source['name']} (events={len(published_events)} queued={len(review_queue)})")

    print("\n💾 Sauvegarde des bases de données en JSON et CSV...")
    
    save_json(review_queue, data_path("review_queue.json"))
    save_json(published_events, data_path("events.json"))
    save_json(not_events, data_path("not_events.json"))
    
    save_csv(review_queue, data_path("review_queue.csv"))
    save_csv(published_events, data_path("events.csv"))
    save_csv(not_events, data_path("not_events.csv"))
    
    save_seen_urls(seen_urls)
    update_last_run()
    
    print("PIPELINE DONE !")

if __name__ == "__main__":
    run_pipeline()