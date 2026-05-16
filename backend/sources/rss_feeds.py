# sources/rss_feeds.py
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime

def fetch(source_config):
    print(f"Scraping RSS: {source_config['name']}")
    raw_events = []
    feed = feedparser.parse(source_config['url'])

    # articles_limit = source_config.get('articles_limit', 15)
    
    for entry in feed.entries:
    # for entry in feed.entries[:articles_limit]:
        soup = BeautifulSoup(entry.get('summary', ''), 'html.parser')
        clean_text = soup.get_text(separator=' ', strip=True)
        
        raw_events.append({
            "source": source_config['name'],
            "source_url": source_config['url'],
            "scraped_at": datetime.now().isoformat(),
            "raw_text": clean_text,
            "title": entry.get('title', ''),
            "url": entry.get('link', ''),
            "date_str": None,           # conforme spec (peut être null)
            "location_str": ""          # conforme spec (chaîne vide)
        })
    return raw_events