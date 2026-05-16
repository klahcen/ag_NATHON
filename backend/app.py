import streamlit as st
import json
import os
from datetime import datetime

# -------------------------------------------------------------------
# Configuration de la page
# -------------------------------------------------------------------
st.set_page_config(
    page_title="InsureNow | Curator",
    page_icon="public/logo/insurenow_logo.svg",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------------
# Design Custom CSS (Inspiré de vos maquettes Modern Dashboard)
# -------------------------------------------------------------------
st.markdown("""
    <style>
    /* Import de la police Poppins pour un look très moderne */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

    /* Fond global de l'application (Gris très clair) */
    .stApp {
        background-color: #F4F7FE;
        font-family: 'Poppins', sans-serif;
    }
    
    /* Cacher les éléments inutiles de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Réduire l'espace en haut */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* --- TYPOGRAPHIE --- */
    h1 {
        color: #2B3674;
        font-weight: 700;
        font-size: 2.2rem;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        color: #A3AED0;
        font-weight: 500;
        font-size: 1rem;
        margin-bottom: 2rem;
    }

    /* --- CARTES STATISTIQUES (Top Row) --- */
    .stat-container {
        display: flex;
        gap: 20px;
        margin-bottom: 30px;
    }
    .stat-card {
        background-color: #FFFFFF;
        border-radius: 20px;
        padding: 20px 25px;
        flex: 1;
        box-shadow: 0 10px 20px rgba(226, 232, 240, 0.4);
        display: flex;
        flex-direction: column;
    }
    .stat-title {
        color: #A3AED0;
        font-size: 0.9rem;
        font-weight: 500;
    }
    .stat-value {
        color: #2B3674;
        font-size: 2rem;
        font-weight: 700;
        margin-top: 5px;
    }
    
    .stat-card.active {
        background: linear-gradient(135deg, #FF9B8A 0%, #FF6B52 100%); /* Corail vibrant */
    }
    .stat-card.active .stat-title, .stat-card.active .stat-value {
        color: #FFFFFF;
    }

    /* --- CARTE APERÇU (Rendu Final) --- */
    .event-preview-card {
        background: linear-gradient(135deg, #868CFF 0%, #4318FF 100%); /* Bleu/Violet moderne */
        border-radius: 20px;
        padding: 35px;
        color: white;
        box-shadow: 0 15px 30px rgba(67, 24, 255, 0.15);
        margin-bottom: 30px;
        position: relative;
        overflow: hidden;
    }
    /* Décoration en arrière-plan de la carte */
    .event-preview-card::after {
        content: '';
        position: absolute;
        top: -50px;
        right: -50px;
        width: 150px;
        height: 150px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 50%;
    }
    .ep-meta {
        font-size: 0.85rem;
        font-weight: 500;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: #E2E8F0;
        margin-bottom: 15px;
        display: flex;
        justify-content: space-between;
    }
    .ep-title {
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 20px;
        line-height: 1.3;
    }
    .ep-tags {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-bottom: 25px;
    }
    .ep-tag {
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(5px);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    .ep-desc {
        background: rgba(0, 0, 0, 0.2);
        padding: 20px;
        border-radius: 15px;
        font-style: italic;
        font-size: 0.95rem;
        border-left: 4px solid #FFD166;
    }

    /* --- FORMULAIRE D'ÉDITION --- */
    [data-testid="stForm"] {
        background-color: #FFFFFF;
        border: none;
        border-radius: 20px;
        padding: 35px;
        box-shadow: 0 10px 30px rgba(226, 232, 240, 0.4);
    }
    
    /* Labels des inputs */
    .stTextInput > label, .stSelectbox > label, .stMultiSelect > label, .stTextArea > label {
        color: #2B3674 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }
    
    /* Inputs arrondis */
    .stTextInput input, .stTextArea textarea {
        border-radius: 12px !important;
        border: 1px solid #E2E8F0 !important;
        background-color: #F8FAFC !important;
        color: #2B3674 !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #4318FF !important;
        box-shadow: 0 0 0 1px #4318FF !important;
    }

    /* --- BOUTONS --- */
    .stButton > button {
        border-radius: 12px;
        font-weight: 600;
        padding: 0.6rem 1.5rem;
        border: none;
        transition: all 0.2s;
    }
    
    /* Bouton Publier (Couleur principale) */
    .btn-publish > .stButton > button {
        background-color: #4318FF;
        color: white;
        width: 100%;
    }
    .btn-publish > .stButton > button:hover { background-color: #3311CC; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(67, 24, 255, 0.3);}
    
    /* Bouton Rejeter (Rouge Corail) */
    .btn-reject > .stButton > button {
        background-color: #FFECE8;
        color: #FF6B52;
        width: 100%;
    }
    .btn-reject > .stButton > button:hover { background-color: #FF6B52; color: white; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(255, 107, 82, 0.3);}

    /* --- SIDEBAR --- */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: none;
        box-shadow: 5px 0 20px rgba(226, 232, 240, 0.4);
    }
    .sidebar-menu-item {
        padding: 12px 20px;
        color: #A3AED0;
        font-weight: 600;
        font-size: 1rem;
        border-radius: 12px;
        margin-bottom: 8px;
        cursor: pointer;
    }
    .sidebar-menu-item.active {
        background-color: #4318FF;
        color: #FFFFFF;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# Fonctions de gestion des données
# -------------------------------------------------------------------
def load_data(filepath):
    if not os.path.exists(filepath): return []
    with open(filepath, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return []

def save_data(data, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def process_event(event_data, action):
    queue = load_data("data/review_queue.json")
    published = load_data("data/events.json")
    rejected = load_data("data/not_events.json")
    
    queue = [e for e in queue if e.get("event_id") != event_data["event_id"]]
    
    if action == "publish":
        event_data["status"] = "published"
        event_data["last_verified_at"] = datetime.now().isoformat()
        published.append(event_data)
        save_data(published, "data/events.json")
    elif action == "reject":
        rejected.append({
            "title": event_data["title"],
            "url": event_data["url"],
            "source": event_data["source"],
            "rejected_at": datetime.now().isoformat(),
            "reason": "Rejected by human curator"
        })
        save_data(rejected, "data/not_events.json")
        
    save_data(queue, "data/review_queue.json")
    st.rerun()

# -------------------------------------------------------------------
# Chargement des données
# -------------------------------------------------------------------
queue_events = load_data("data/review_queue.json")
published_events = load_data("data/events.json")

# -------------------------------------------------------------------
# UI : Menu Latéral (Sidebar)
# -------------------------------------------------------------------
with st.sidebar:
    st.image("public/logo/insurenow_logo.svg", use_container_width=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class="sidebar-menu-item active">Dashboard</div>
        <div class="sidebar-menu-item">Analytics</div>
        <div class="sidebar-menu-item">Sources</div>
        <div class="sidebar-menu-item">Settings</div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    if st.button("Actualiser les données", use_container_width=True):
        st.rerun()

# -------------------------------------------------------------------
# UI : Zone Principale
# -------------------------------------------------------------------
st.markdown("<h1>Modération Événements</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Validez et éditez les opportunités détectées par l'IA.</div>", unsafe_allow_html=True)

# Ligne de statistiques
st.markdown(f"""
    <div class="stat-container">
        <div class="stat-card active">
            <div class="stat-title">ÉVÉNEMENTS EN ATTENTE</div>
            <div class="stat-value">{len(queue_events)}</div>
        </div>
        <div class="stat-card">
            <div class="stat-title">PUBLIÉS SUR LE SITE</div>
            <div class="stat-value">{len(published_events)}</div>
        </div>
        <div class="stat-card">
            <div class="stat-title">MISE À JOUR</div>
            <div class="stat-value" style="font-size:1.2rem; margin-top:15px;">Aujourd'hui</div>
        </div>
    </div>
""", unsafe_allow_html=True)

if not queue_events:
    st.success("Excellent travail ! Aucun événement en attente de modération.")
else:
    current_event = queue_events[0]
    
    # Préparation des variables pour l'affichage
    city = current_event.get("location", {}).get("city", "Non spécifié")
    if city is None: city = "Lieu non spécifié"
    date_str = current_event.get('start_date', 'Date inconnue')
    source_str = current_event.get('source', 'Source').upper()
    
    # Création des tags visuels (HTML)
    tags_html = "".join([f"<span class='ep-tag'>{tag.upper()}</span>" for tag in current_event.get("topics", [])])
    if not tags_html: tags_html = "<span class='ep-tag'>TECH</span>"

    # --- SECTION : Carte d'Aperçu (Design Inspiré) ---
    st.markdown(f"""
        <div class="event-preview-card">
            <div class="ep-meta">
                <span>{date_str} • {city.upper()}</span>
                <span>{source_str}</span>
            </div>
            <div class="ep-title">{current_event.get('title', '')}</div>
            <div class="ep-tags">
                {tags_html}
            </div>
            <div class="ep-desc">"{current_event.get('why_relevant', 'Aucune accroche générée.')}"</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"<div style='text-align: right; margin-bottom: 20px;'><a href='{current_event['url']}' target='_blank' style='color: #4318FF; font-weight: 600; text-decoration: none;'>Voir l'article original ↗</a></div>", unsafe_allow_html=True)

    # --- SECTION : Formulaire d'Édition ---
    with st.form("edit_event_form"):
        col_left, col_right = st.columns(2)
        
        with col_left:
            edited_title = st.text_input("Titre public", value=current_event.get("title", ""))
            edited_date = st.text_input("Date (AAAA-MM-JJ)", value=current_event.get("start_date", ""))
            edited_city = st.text_input("Ville / Lieu", value=city)
            
        with col_right:
            allowed_topics = ['fundraising', 'saas_b2b', 'ai', 'security_compliance', 'international_growth', 'founder_community', 'deeptech']
            current_topics = [t for t in current_event.get("topics", []) if t in allowed_topics]
            edited_topics = st.multiselect("Sujets prioritaires", options=allowed_topics, default=current_topics)
            
            allowed_stages = ['pre_seed', 'seed', 'series_a', 'series_b_plus', 'all']
            current_stages = current_event.get("relevant_for", {}).get("stages", [])
            edited_stages = st.multiselect("Stades de maturité", options=allowed_stages, default=current_stages)
            
        edited_why = st.text_area("Accroche éditoriale (Pourquoi y aller ?)", value=current_event.get("why_relevant", ""))
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Boutons d'action alignés
        col_btn1, col_btn2, _ = st.columns([1, 1, 2])
        
        with col_btn1:
            st.markdown('<div class="btn-publish">', unsafe_allow_html=True)
            submit_publish = st.form_submit_button("Publier l'événement")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_btn2:
            st.markdown('<div class="btn-reject">', unsafe_allow_html=True)
            submit_reject = st.form_submit_button("Rejeter")
            st.markdown('</div>', unsafe_allow_html=True)

        # Logique de traitement
        if submit_publish:
            current_event["title"] = edited_title
            current_event["start_date"] = edited_date
            if "location" not in current_event: current_event["location"] = {}
            current_event["location"]["city"] = edited_city
            current_event["topics"] = edited_topics
            if "relevant_for" not in current_event: current_event["relevant_for"] = {}
            current_event["relevant_for"]["stages"] = edited_stages
            current_event["why_relevant"] = edited_why
            process_event(current_event, "publish")
            
        if submit_reject:
            process_event(current_event, "reject")