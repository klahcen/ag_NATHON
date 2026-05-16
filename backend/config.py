# config.py

AGENT_CONFIG = {
    "icp_definition": {
        "company_stages": ['pre_seed', 'seed', 'series_a', 'series_b_plus'],
        "activities": ['saas', 'fintech', 'healthtech', 'ai_product', 'marketplace', 'devtools', 'cyber'],
        "geographies": ['FR', 'EU', 'UK']
    },
    "topic_priorities": {
        "fundraising": 'high',
        "saas_b2b": 'high',
        "ai_and_ai_act": 'high',
        "security_compliance": 'high',
        "international_growth": 'medium',
        "founder_community": 'medium',
        "deeptech": 'medium'
    },
    # La fenêtre de validité des événements
    "freshness_window": { 
        "past_days": 14, 
        "future_days": 180 
    }
}

# La liste complète issue de la User Story
SOURCE_LIST = [
    {"name": "Maddyness", "url": "https://www.maddyness.com/feed/", "type": "rss", "parser_id": "rss_parser", "enabled": True, "trust_level": "medium"},
    {"name": "FrenchWeb", "url": "https://www.frenchweb.fr/feed/", "type": "rss", "parser_id": "rss_parser", "enabled": True, "trust_level": "medium"},
    {"name": "Station F", "url": "https://stationf.co/events", "type": "html_scrape", "parser_id": "web_scrapers", "enabled": True, "trust_level": "high"},
    {"name": "BPI Calendar", "url": "https://evenements.bpifrance.fr/", "type": "html_scrape", "parser_id": "web_scrapers", "enabled": True, "trust_level": "high"},
    {"name": "La French Tech", "url": "https://lafrenchtech.com/fr/agenda/", "type": "html_scrape", "parser_id": "web_scrapers", "enabled": True, "trust_level": "high"},
    {"name": "Bpifrance Le Hub", "url": "https://lehub.bpifrance.fr/events", "type": "html_scrape", "parser_id": "web_scrapers", "enabled": True, "trust_level": "high"},
    {"name": "Hello Tomorrow", "url": "https://hello-tomorrow.org/events/", "type": "html_scrape", "parser_id": "web_scrapers", "enabled": True, "trust_level": "medium"},
    {"name": "Sifted Events", "url": "https://sifted.eu/feed", "type": "rss", "parser_id": "rss_parser", "enabled": True, "trust_level": "high"},
    {"name": "Tech.eu", "url": "https://tech.eu/feed", "type": "rss", "parser_id": "rss_parser", "enabled": True, "trust_level": "high"},
    {"name": "Eventbrite Paris (Startups & Tech)", "url": "https://www.eventbrite.com/d/france--paris/all-events/?subcategories=1001&page=1", "type": "html", "parser_id": "eventbrite_scrapers", "enabled": True, "trust_level": "medium"},
    {"name": "Lu.ma Paris", "url": "https://lu.ma/paris", "type": "html", "parser_id": "web_scrapers", "enabled": True, "trust_level": "high"},

    # SOURCES EXPERIMENTALES (Commentées par défaut)
    # {"name": "Meetup - Startups Paris","url": "https://www.meetup.com/fr-FR/find/?keywords=startup&location=fr--Paris&source=EVENTS","type": "html","parser_id": "experimental_scrapers","platform": "meetup","enabled": True,"trust_level": "medium"},
    # {"name": "Billetweb - Business","url": "https://www.billetweb.fr/recherche?category=business","type": "html","parser_id": "experimental_scrapers","platform": "billetweb","enabled": True,"trust_level": "medium"},
    # {"name": "Weezevent - Conférences","url": "https://weezevent.com/fr/","type": "html","parser_id": "experimental_scrapers","platform": "weezevent","enabled": True,"trust_level": "medium"},
]