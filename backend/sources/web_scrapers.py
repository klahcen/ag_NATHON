# sources/web_scrapers.py
import re
from datetime import datetime
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def fetch(source_config):
    """
    Scraper universel utilisant Playwright.
    Optimisé pour lire les cartes d'événements complexes (ex: Station F).
    """
    events = []
    name = source_config['name']
    url = source_config['url']
    
    print(f"      🔍 Lancement du scraper intelligent pour {name}...")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(3000)
            
            link_elements = page.locator("a").all()
            
            for element in link_elements:
                try:
                    href = element.get_attribute("href")
                    title = element.inner_text().strip()
                    
                    if not href:
                        continue
                        
                    href_lower = href.lower()
                    is_event_link = False
                    raw_context = ""
                    
                    # --- EXTRACTION INTELLIGENTE DE LA CARTE (Basée sur le DOM Station F) ---
                    # On nettoie le titre des caractères spéciaux comme la flèche "↗"
                    clean_text_check = re.sub(r'[^a-zA-Z]', '', title).upper()
                    
                    if clean_text_check in ['REGISTER', 'SPACES', 'BILLETS', 'RSVP', 'SINSCRIRE', 'PARTICIPER'] or len(title) < 5:
                        try:
                            # On remonte chercher le conteneur flex-col vu dans l'inspecteur
                            card_text = element.evaluate("""el => { 
                                const parent = el.closest('div.flex-col, .card, article, [role="listitem"]'); 
                                return parent ? parent.innerText : ''; 
                            }""")
                            if card_text:
                                raw_context = card_text
                                lines = [line.strip() for line in card_text.split('\n') if len(line.strip()) > 3]
                                if lines:
                                    title = lines[0] # Capture le texte du <h3>
                        except Exception:
                            pass
                    
                    if len(title) < 4:
                        continue
                    
                    # --- FILTRES DE SOURCES ---
                    if name == 'Station F':
                        exclusions = ['facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com', 'mailto:', '/news']
                        if not any(ex in href_lower for ex in exclusions):
                            if 'stationf.co' not in href_lower or '/events/' in href_lower:
                                is_event_link = True
                                
                    elif name == 'Bpifrance Le Hub' or name == 'BPI Calendar':
                        if '/evenements/' in href_lower or '/event/' in href_lower or '/evenement/' in href_lower:
                            is_event_link = True
                            
                    elif name == 'La French Tech':
                        if '/agenda/' in href_lower or '/evenement/' in href_lower:
                            is_event_link = True
                            
                    elif name == 'Hello Tomorrow':
                        if '/events/' in href_lower:
                            is_event_link = True
                            
                    elif 'Lu.ma' in name or 'Luma' in name:
                        exclusions = ['/discover', '/create', '/login', '/signin', '/about', '/pricing', '/home']
                        if not any(ex in href_lower for ex in exclusions):
                            if 'evt-' in href_lower:
                                is_event_link = True
                            elif href.startswith('/') and len(href) > 5 and len(title) >= 10:
                                is_event_link = True

                    # --- SAUVEGARDE ---
                    if is_event_link:
                        if href.startswith('http'): full_url = href
                        elif href.startswith('?'): full_url = f"{url}{href}"
                        else: full_url = f"https://{url.split('/')[2]}{href}"
                            
                        clean_title = re.sub(r'\s+', ' ', title)
                        
                        events.append({
                            "title": clean_title,
                            "raw_text": f"Titre: {clean_title}\nContexte carte: {raw_context}",
                            "url": full_url,
                            "source": name,
                            "scraped_at": datetime.now().isoformat()
                        })
                except Exception:
                    continue
                    
            browser.close()
            events = list({e['url']: e for e in events}.values())
            print(f"      ✅ {len(events)} vrais événements trouvés sur {name}.")
            
    except PlaywrightTimeoutError:
        print(f"      ❌ Erreur : Timeout sur {name}.")
    except Exception as e:
        print(f"      ❌ Erreur technique sur {name} : {e}")

    return events