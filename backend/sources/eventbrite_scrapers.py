# sources/eventbrite_scrapers.py
import re
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def fetch(source_config):
    """
    Scraper dédié à Eventbrite utilisant Playwright.
    Cible spécifiquement la structure d'URL /e/ + ID.
    """
    events = []
    name = source_config['name']
    url = source_config['url']
    
    print(f"      🔍 Lancement du scraper Eventbrite pour {name}...")

    try:
        with sync_playwright() as p:
            # On utilise headless=True. Si Eventbrite bloque trop souvent, 
            # passer temporairement à headless=False peut aider à passer sous le radar.
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Délai court pour éviter de rester bloqué sur Datadome (le Captcha d'Eventbrite)
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            
            # Petite pause pour laisser les cartes d'événements charger
            page.wait_for_timeout(3000)
            
            link_elements = page.locator("a").all()
            
            for element in link_elements:
                try:
                    href = element.get_attribute("href")
                    # On tente de récupérer le texte, ou le aria-label (très utilisé par Eventbrite)
                    title = element.inner_text().strip()
                    if not title:
                        title = element.get_attribute("aria-label") or ""
                    
                    if not href or len(title) < 5:
                        continue
                        
                    href_lower = href.lower()
                    
                    # --- LE FILTRE DÉCOUVERT PAR VOTRE ANALYSE ---
                    # 1. Contient "/e/"
                    # 2. Contient une longue suite de chiffres (l'ID de l'événement)
                    if '/e/' in href_lower and re.search(r'\d{10,}', href_lower):
                        
                        # Nettoyage de l'URL : on retire tout ce qui se trouve après le "?" (les trackers d'affiliation)
                        clean_url = href.split('?')[0]
                        
                        # Reconstruction de l'URL absolue si Eventbrite donne un chemin relatif
                        if clean_url.startswith('/'):
                            clean_url = f"https://www.eventbrite.fr{clean_url}"
                            
                        clean_title = re.sub(r'\s+', ' ', title)
                        
                        events.append({
                            "title": clean_title,
                            "raw_text": f"Eventbrite : {clean_title}",
                            "url": clean_url,
                            "source": name,
                            "scraped_at": datetime.now().isoformat()
                        })
                except Exception:
                    continue
                    
            browser.close()
            
            # Déduplication basée sur l'URL nettoyée
            events = list({e['url']: e for e in events}.values())
            print(f"      ✅ {len(events)} vrais événements trouvés sur {name}.")
            
    except PlaywrightTimeoutError:
        print(f"      ❌ Erreur : Timeout sur {name} (Blocage anti-bot probable).")
    except Exception as e:
        print(f"      ❌ Erreur technique sur {name} : {e}")

    return events