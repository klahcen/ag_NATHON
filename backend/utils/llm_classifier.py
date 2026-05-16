import os
import json
import re
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# -------------------------------------------------------------------
# Allowed enums (strict validation)
# -------------------------------------------------------------------
ALLOWED_TOPICS = {
    'fundraising', 'saas_b2b', 'ai', 'security_compliance',
    'international_growth', 'founder_community', 'deeptech'
}
ALLOWED_STAGES = {'pre_seed', 'seed', 'series_a', 'series_b_plus', 'all'}
ALLOWED_FORMAT_TAGS = {
    'free', 'paid', 'invite_only', 'application_required',
    'pitch_event', 'workshop', 'conference', 'meetup'
}
ALLOWED_FORMATS = {'in_person', 'online', 'hybrid'}
ALLOWED_LANGUAGES = {'FR', 'EN', 'multi'}

# -------------------------------------------------------------------
# System prompt amélioré
# -------------------------------------------------------------------
SYSTEM_PROMPT = """
You are a strict but pragmatic event curator for tech startup founders (Base Camp Insurenow).

Given a raw event text, extract structured information.

IMPORTANT:
- If the text is clearly NOT a tech/startup/founder/entrepreneur event (ex: pure real estate, fashion show, music festival without tech angle), return empty JSON: {}
- Networking events, meetups, workshops, AI nights, founder events, etc. ARE considered relevant.

STRICT RULES (use only these values):
- 'topics': list from ['fundraising','saas_b2b','ai','security_compliance','international_growth','founder_community','deeptech']
- 'relevant_stages': list from ['pre_seed','seed','series_a','series_b_plus','all']
- 'activities': list of strings (e.g. ['networking','ai','saas']). Default ['all']
- 'format_tags': list from allowed tags
- 'format': 'in_person' | 'online' | 'hybrid'
- 'timezone': IANA name, default 'Europe/Paris'
- 'language': 'FR', 'EN', or 'multi'
- 'end_date': YYYY-MM-DD or null
- 'why_relevant': one short editorial sentence (max 140 chars). Base it only on the source.

Reply ONLY with valid JSON. No explanation.
"""

def make_user_prompt(raw_event: dict) -> str:
    return f"""
Title: {raw_event.get('title', '')}
Text: {raw_event.get('raw_text', '')}

Expected JSON structure (all fields must be present):
{{
  "title": "Clean title",
  "description": "Short description max 280 chars",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD or null",
  "timezone": "Europe/Paris",
  "format": "in_person|online|hybrid",
  "location_city": "City or null",
  "location_country": "Country or null",
  "location_venue": "Venue or null",
  "language": "FR|EN|multi",
  "topics": [],
  "relevant_stages": [],
  "activities": ["all"],
  "format_tags": [],
  "why_relevant": "..."
}}
"""


def extract_first_json(text: str) -> dict | None:
    """Extract the first valid JSON object from LLM response.

    Returns None when no parseable JSON was found (caller should retry).
    Returns {} when the model intentionally returned an empty object (not an event).
    """
    text = text.strip()

    # Nettoyage markdown
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    start = text.find('{')
    if start == -1:
        return None

    # Recherche équilibrée des accolades
    brace_count = 0
    end = start
    for i, ch in enumerate(text[start:], start):
        if ch == '{':
            brace_count += 1
        elif ch == '}':
            brace_count -= 1
            if brace_count == 0:
                end = i
                break
    else:
        return None

    try:
        parsed = json.loads(text[start : end + 1])
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def validate_and_clean(data: dict) -> dict:
    """Validation stricte + nettoyage."""
    if not isinstance(data, dict) or not data:
        return {}

    cleaned = {
        "title": str(data.get("title", "")).strip()[:200],
        "description": str(data.get("description", "")).strip()[:280],
        "start_date": data.get("start_date"),
        "end_date": data.get("end_date"),
        "timezone": str(data.get("timezone", "Europe/Paris")),
        "format": data.get("format"),
        "location_city": data.get("location_city"),
        "location_country": data.get("location_country"),
        "location_venue": data.get("location_venue"),
        "language": data.get("language", "FR"),
        "topics": [],
        "relevant_stages": [],
        "activities": ["all"],
        "format_tags": [],
        "why_relevant": str(data.get("why_relevant", "")).strip()[:200],
    }

    # Validation listes
    if isinstance(data.get("topics"), list):
        cleaned["topics"] = [t for t in data["topics"] if t in ALLOWED_TOPICS]
    
    if isinstance(data.get("relevant_stages"), list):
        cleaned["relevant_stages"] = [s for s in data["relevant_stages"] if s in ALLOWED_STAGES]
    
    if isinstance(data.get("activities"), list):
        cleaned["activities"] = [a for a in data["activities"] if isinstance(a, str)] or ["all"]
    
    if isinstance(data.get("format_tags"), list):
        cleaned["format_tags"] = [f for f in data["format_tags"] if f in ALLOWED_FORMAT_TAGS]

    # Format & language
    if cleaned["format"] not in ALLOWED_FORMATS:
        cleaned["format"] = "in_person"  # default plus permissif
    
    if cleaned["language"] not in ALLOWED_LANGUAGES:
        cleaned["language"] = "FR"

    # Dates
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    for field in ["start_date", "end_date"]:
        val = cleaned.get(field)
        if val and not date_pattern.match(str(val)):
            cleaned[field] = None

    if cleaned["end_date"] is None and cleaned["start_date"]:
        cleaned["end_date"] = cleaned["start_date"]

    # Rejet seulement si pas de titre ou pas de date du tout
    if not cleaned["title"] or not cleaned["start_date"]:
        return {}

    return cleaned


def classify_event(raw_event: dict, max_attempts: int = 3) -> dict:
    """
    Version améliorée avec meilleure gestion des rejets.
    """
    title = raw_event.get('title', '')[:80]

    for attempt in range(max_attempts):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",   # Modèle plus récent et fiable
                max_tokens=1200,
                temperature=0.1,                     # Légèrement > 0 pour meilleure extraction
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": make_user_prompt(raw_event)}]
            )

            raw_text = response.content[0].text.strip()
            parsed = extract_first_json(raw_text)

            if parsed is None:
                print(f"      ⚠️ Tentative {attempt + 1}/{max_attempts} : {title[:60]}... (pas de JSON valide)")
                continue

            if parsed == {}:
                print(f"      ⏭️ Non-événement : {title[:70]}...")
                return {}

            validated = validate_and_clean(parsed)

            if validated:
                print(f"      ✅ Accepté : {validated['title'][:70]}...")
                return validated

            print(f"      ⚠️ Tentative {attempt + 1}/{max_attempts} : Données incomplètes pour '{title[:50]}...'")

        except Exception as e:
            print(f"      ⚠️ Erreur API (Tentative {attempt + 1}) : {e}")

    print(f"      ❌ Rejet définitif : {title[:70]}...")
    return {}