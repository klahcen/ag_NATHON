# sources/experimental_scrapers.py
import requests
from bs4 import BeautifulSoup

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9"
    }

def fetch_meetup(source):
    print(f"    🧪 [Expérimental] Scraping Meetup : {source['name']}")
    raw_events = []
    try:
        response = requests.get(source['url'], headers=get_headers(), timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        event_cards = soup.find_all('a', id=lambda x: x and x.startswith('event-card-link'))
        for card in event_cards:
            title_tag = card.find('h3')
            if title_tag:
                raw_events.append({"title": title_tag.text.strip(), "url": card.get('href'), "source": source['name']})
        print(f"    ✅ {len(raw_events)} événements trouvés.")
        return raw_events
    except Exception as e:
        print(f"    ❌ Erreur Meetup : {e}")
        return []

def fetch_billetweb(source):
    print(f"    🧪 [Expérimental] Scraping Billetweb : {source['name']}")
    raw_events = []
    try:
        response = requests.get(source['url'], headers=get_headers(), timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        events = soup.find_all('div', class_=lambda c: c and 'event' in c.lower())
        for event in events:
            link = event.find('a', href=True)
            if link and "billetweb.fr" in link['href']:
                raw_events.append({"title": link.text.strip(), "url": link['href'], "source": source['name']})
        print(f"    ✅ {len(raw_events)} événements trouvés.")
        return raw_events
    except Exception as e:
        print(f"    ❌ Erreur Billetweb : {e}")
        return []

def fetch_weezevent(source):
    print(f"    🧪 [Expérimental] Scraping Weezevent : {source['name']}")
    raw_events = []
    try:
        response = requests.get(source['url'], headers=get_headers(), timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Structure classique Weezevent (simplifiée pour le test)
        links = soup.find_all('a', href=True)
        for link in links:
            if "weezevent.com/fr/widget_billeterie" in link['href'] or "my.weezevent.com" in link['href']:
                title = link.text.strip()
                if len(title) > 5:
                    raw_events.append({"title": title, "url": link['href'], "source": source['name']})
        print(f"    ✅ {len(raw_events)} événements trouvés.")
        return raw_events
    except Exception as e:
        print(f"    ❌ Erreur Weezevent : {e}")
        return []

def fetch(source):
    """Le routeur interne pour les sources expérimentales"""
    platform = source.get('platform')
    
    if platform == 'meetup':
        return fetch_meetup(source)
    elif platform == 'billetweb':
        return fetch_billetweb(source)
    elif platform == 'weezevent':
        return fetch_weezevent(source)
    else:
        print(f"    ⚠️ Plateforme expérimentale inconnue : {platform}")
        return []