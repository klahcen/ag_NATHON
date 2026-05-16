"use client";

import { useState, useEffect, useMemo } from "react";
import { 
  CheckCircle, XCircle, LayoutDashboard, Settings, Database, Activity, 
  MapPin, Calendar as CalendarIcon, ExternalLink, Search, Filter, AlertTriangle, Bell,
  ChevronLeft, ChevronRight // NOUVELLES ICÔNES POUR LA PAGINATION
} from "lucide-react";
import { getApiBase } from "@/lib/api";

// --- TYPES ---
type Event = {
  event_id: string;
  title: string;
  start_date: string;
  source: string;
  url: string;
  location?: { city: string };
  topics?: string[];
  why_relevant?: string;
  status: string;
};

export default function CuratorDashboard() {
  // --- ÉTATS (STATE) ---
  const [activeTab, setActiveTab] = useState("queue");
  const [queue, setQueue] = useState<Event[]>([]);
  const [published, setPublished] = useState<Event[]>([]);
  const [rejected, setRejected] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);

  // NOUVEAU : État pour la page actuelle
  const [currentPage, setCurrentPage] = useState(1);

  // États pour les filtres et la recherche
  const [searchTerm, setSearchTerm] = useState("");
  const [filterCity, setFilterCity] = useState("");
  const [filterSource, setFilterSource] = useState("");
  
  // États pour la modale de confirmation
  const [confirmModal, setConfirmModal] = useState<{isOpen: boolean, action: string, eventId: string | null, title: string}>({
    isOpen: false, action: "", eventId: null, title: ""
  });

  // --- CHARGEMENT DES DONNÉES ---
  const parseEventList = async (res: Response): Promise<Event[]> => {
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  };

  const fetchEvents = async () => {
    setLoading(true);
    const api = getApiBase();
    try {
      const [resQ, resP, resR] = await Promise.all([
        fetch(`${api}/api/events/queue`),
        fetch(`${api}/api/events/published`),
        fetch(`${api}/api/events/rejected`)
      ]);
      setQueue(await parseEventList(resQ));
      setPublished(await parseEventList(resP));
      setRejected(await parseEventList(resR));
    } catch (error) {
      console.error("Erreur API :", error);
    }
    setLoading(false);
  };

  useEffect(() => { fetchEvents(); }, []);

  // NOUVEAU : Remettre à la page 1 si on change d'onglet ou de filtre
  useEffect(() => {
    setCurrentPage(1);
  }, [activeTab, searchTerm, filterCity, filterSource]);

  // --- LOGIQUE DE FILTRAGE (En temps réel) ET PAGINATION ---
  const currentData = useMemo(() => {
    // 1. Sélectionner la bonne liste selon l'onglet
    const baseList = activeTab === "queue" ? queue : activeTab === "published" ? published : rejected;
    
    // 2. Appliquer les filtres
    return baseList.filter(ev => {
      const matchSearch = ev.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          (ev.why_relevant || "").toLowerCase().includes(searchTerm.toLowerCase());
      const matchCity = filterCity ? ev.location?.city === filterCity : true;
      const matchSource = filterSource ? ev.source === filterSource : true;
      return matchSearch && matchCity && matchSource;
    });
  }, [activeTab, queue, published, rejected, searchTerm, filterCity, filterSource]);

  // 3. Calculer les éléments à afficher pour la page actuelle
  const limit = activeTab === "rejected" ? 20 : 6;
  const totalPages = Math.ceil(currentData.length / limit) || 1;
  const paginatedData = currentData.slice((currentPage - 1) * limit, currentPage * limit);

  // Extraire les listes uniques pour les menus déroulants
  const uniqueCities = Array.from(new Set(queue.map(ev => ev.location?.city).filter(Boolean)));
  const uniqueSources = Array.from(new Set(queue.map(ev => ev.source).filter(Boolean)));

  // --- ACTIONS ET MODALES ---
  const requestAction = (eventId: string, action: string, title: string) => {
    setConfirmModal({ isOpen: true, action, eventId, title });
  };

  const confirmAndExecuteAction = async () => {
    if (confirmModal.action === "refresh") {
      await fetchEvents();
    } else if (confirmModal.eventId) {
      try {
        await fetch(`${getApiBase()}/api/events/action`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ event_id: confirmModal.eventId, action: confirmModal.action })
        });
        await fetchEvents();
      } catch (error) {
        console.error("Erreur lors de l'action :", error);
      }
    }
    setConfirmModal({ isOpen: false, action: "", eventId: null, title: "" });
  };

  // --- GÉNÉRATION DU MINI CALENDRIER ---
  const renderCalendar = () => {
    const days = ["Lu", "Ma", "Me", "Je", "Ve", "Sa", "Di"];
    const dates = Array.from({length: 31}, (_, i) => i + 1);
    const today = new Date().getDate();

    return (
      <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 mb-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-bold text-[#0F172A]">Mai 2026</h3>
          <div className="text-xs font-semibold text-[#4318FF] bg-indigo-50 px-2 py-1 rounded-md">Aujourd'hui</div>
        </div>
        <div className="grid grid-cols-7 gap-2 text-center text-xs mb-2 text-slate-400 font-medium">
          {days.map(d => <div key={d}>{d}</div>)}
        </div>
        <div className="grid grid-cols-7 gap-2 text-center text-sm">
          <div className="p-1"></div><div className="p-1"></div><div className="p-1"></div><div className="p-1"></div>
          {dates.map(d => (
            <div key={d} className={`p-1.5 rounded-lg flex items-center justify-center font-medium ${d === today ? 'bg-[#4318FF] text-white shadow-md' : 'text-slate-600 hover:bg-slate-50 cursor-pointer'}`}>
              {d}
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[#F4F7FE] font-sans text-slate-800">
      
      {/* --- MODALE DE CONFIRMATION --- */}
      {confirmModal.isOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl animate-in fade-in zoom-in duration-200">
            <div className="flex items-center gap-4 mb-4">
              <div className={`p-3 rounded-full ${confirmModal.action === 'reject' ? 'bg-red-100 text-red-600' : 'bg-indigo-100 text-[#4318FF]'}`}>
                <AlertTriangle size={24} />
              </div>
              <div>
                <h3 className="text-xl font-bold text-slate-900">Confirmer l'action</h3>
                <p className="text-slate-500 text-sm">Êtes-vous sûr de vouloir {confirmModal.action === 'publish' ? 'publier' : confirmModal.action === 'reject' ? 'rejeter' : 'actualiser'} ?</p>
              </div>
            </div>
            {confirmModal.title && (
              <div className="bg-slate-50 p-3 rounded-lg text-sm font-medium text-slate-700 mb-6 border border-slate-100">
                "{confirmModal.title}"
              </div>
            )}
            <div className="flex gap-3 justify-end mt-6">
              <button onClick={() => setConfirmModal({isOpen: false, action: "", eventId: null, title: ""})} className="px-4 py-2 font-semibold text-slate-500 hover:bg-slate-100 rounded-lg transition-colors">
                Annuler
              </button>
              <button onClick={confirmAndExecuteAction} className={`px-4 py-2 font-semibold text-white rounded-lg transition-colors ${confirmModal.action === 'reject' ? 'bg-red-500 hover:bg-red-600' : 'bg-[#4318FF] hover:bg-[#3311CC]'}`}>
                Confirmer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* --- SIDEBAR GAUCHE (Navigation) --- */}
      <aside className="w-64 bg-[#0F172A] text-slate-300 flex flex-col flex-shrink-0">
        <div className="h-24 flex items-center justify-center pl-7 pr-8 border-b border-slate-800">
          <img 
            src="/logo/insurenow_logo.svg" 
            alt="InsureNow Logo" 
            className="h-24 w-auto filter brightness-0 invert mt-2"
          />
        </div>
        <nav className="flex-1 px-4 py-8 space-y-2">
          <div className="px-4 text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Menu Principal</div>
          <a href="#" className="flex items-center gap-3 px-4 py-3 bg-[#4318FF]/10 text-white rounded-xl font-medium border-l-4 border-[#4318FF]">
            <LayoutDashboard size={20} className="text-[#4318FF]" /> Dashboard
          </a>
          <a href="#" className="flex items-center gap-3 px-4 py-3 hover:text-white hover:bg-white/5 rounded-xl font-medium transition-colors border-l-4 border-transparent">
            <Database size={20} /> Sources
          </a>
          <a href="#" className="flex items-center gap-3 px-4 py-3 hover:text-white hover:bg-white/5 rounded-xl font-medium transition-colors border-l-4 border-transparent">
            <Activity size={20} /> Analytics
          </a>
        </nav>
        <div className="p-4 border-t border-slate-800">
          <a href="#" className="flex items-center gap-3 px-4 py-3 hover:text-white hover:bg-white/5 rounded-xl font-medium transition-colors">
            <Settings size={20} /> Settings
          </a>
        </div>
      </aside>

      {/* --- CONTENU CENTRAL --- */}
      <main className="flex-1 overflow-y-auto px-8 py-8 flex flex-col">
        
        {/* Header avec Barre de recherche */}
        <header className="flex justify-between items-center mb-10">
          <div>
            <h2 className="text-3xl font-bold text-[#0F172A]">Good Morning, Nathan</h2>
            <p className="text-slate-500 mt-1 font-medium">Nouveaux événements détectés par l'Agent.</p>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
              <input 
                type="text" 
                placeholder="Rechercher un événement..." 
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#4318FF]/20 focus:border-[#4318FF] w-72 shadow-sm transition-all"
              />
            </div>
            <button className="p-2.5 bg-white border border-slate-200 rounded-xl text-slate-500 hover:text-[#4318FF] shadow-sm">
              <Bell size={20} />
            </button>
            <button onClick={() => requestAction("", "refresh", "Actualiser toutes les données depuis l'API")} className="bg-[#0F172A] text-white px-5 py-2.5 rounded-xl font-semibold hover:bg-slate-800 shadow-sm transition-all text-sm">
              Actualiser le Radar
            </button>
          </div>
        </header>

        {/* Barre de filtres avancés */}
        <div className="flex gap-4 mb-8 bg-white p-3 rounded-2xl shadow-sm border border-slate-100 items-center">
          <div className="flex items-center gap-2 px-3 text-slate-400 border-r border-slate-100">
            <Filter size={18} /> <span className="text-sm font-semibold">Filtres</span>
          </div>
          
          <select value={filterCity} onChange={(e) => setFilterCity(e.target.value)} className="bg-slate-50 border border-slate-100 text-slate-600 text-sm rounded-lg px-3 py-2 outline-none focus:ring-1 focus:ring-[#4318FF]">
            <option value="">Toutes les villes</option>
            {uniqueCities.map((city: any) => <option key={city} value={city}>{city}</option>)}
          </select>

          <select value={filterSource} onChange={(e) => setFilterSource(e.target.value)} className="bg-slate-50 border border-slate-100 text-slate-600 text-sm rounded-lg px-3 py-2 outline-none focus:ring-1 focus:ring-[#4318FF]">
            <option value="">Toutes les sources</option>
            {uniqueSources.map((src: any) => <option key={src} value={src}>{src}</option>)}
          </select>
          
          <div className="ml-auto flex bg-slate-50 p-1 rounded-lg">
            <button onClick={() => setActiveTab("queue")} className={`px-4 py-1.5 rounded-md text-sm font-semibold transition-colors ${activeTab === "queue" ? "bg-white text-[#4318FF] shadow-sm" : "text-slate-500"}`}>À Modérer ({queue.length})</button>
            <button onClick={() => setActiveTab("published")} className={`px-4 py-1.5 rounded-md text-sm font-semibold transition-colors ${activeTab === "published" ? "bg-white text-[#4318FF] shadow-sm" : "text-slate-500"}`}>Publiés ({published.length})</button>
            <button onClick={() => setActiveTab("rejected")} className={`px-4 py-1.5 rounded-md text-sm font-semibold transition-colors ${activeTab === "rejected" ? "bg-white text-[#4318FF] shadow-sm" : "text-slate-500"}`}>Rejetés</button>
          </div>
        </div>

        {/* GRILLE DE CARTES (3 par ligne) - MODIFIÉ POUR UTILISER paginatedData */}
        {loading ? (
          <div className="flex justify-center items-center py-20 text-[#4318FF] font-semibold animate-pulse">Synchronisation avec l'IA en cours...</div>
        ) : (
          <div className="flex-1">
            <div className="grid grid-cols-1 xl:grid-cols-2 2xl:grid-cols-3 gap-6">
              
              {activeTab === "queue" && paginatedData.map((ev, i) => (
                <div key={i} className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100 hover:shadow-lg transition-shadow flex flex-col h-full relative group">
                  <div className="flex justify-between items-start mb-3">
                    <span className="text-xs font-bold bg-[#4318FF]/10 text-[#4318FF] px-2.5 py-1 rounded-md uppercase tracking-wider">{ev.source}</span>
                    <a href={ev.url} target="_blank" rel="noreferrer" className="text-slate-300 hover:text-[#4318FF] transition-colors"><ExternalLink size={18} /></a>
                  </div>
                  <h3 className="text-lg font-bold text-[#0F172A] leading-snug mb-3 line-clamp-2">{ev.title}</h3>
                  <div className="flex flex-col gap-2 mb-4 text-sm text-slate-500 font-medium">
                    <div className="flex items-center gap-2"><CalendarIcon size={16} className="text-slate-400" /> {ev.start_date || "Date inconnue"}</div>
                    <div className="flex items-center gap-2"><MapPin size={16} className="text-slate-400" /> {ev.location?.city || "Lieu non spécifié"}</div>
                  </div>
                  <div className="bg-slate-50 border-l-2 border-amber-400 p-3 rounded-r-lg mb-4 text-slate-600 text-sm italic flex-grow">
                    "{ev.why_relevant || "Aucune analyse IA disponible."}"
                  </div>
                  <div className="flex gap-2 pt-2">
                    <button onClick={() => requestAction(ev.event_id, "publish", ev.title)} className="flex-1 bg-[#4318FF] hover:bg-[#3311CC] text-white py-2 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 transition-colors">
                      <CheckCircle size={16} /> Valider
                    </button>
                    <button onClick={() => requestAction(ev.event_id, "reject", ev.title)} className="flex-1 bg-rose-50 hover:bg-rose-100 text-rose-600 py-2 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 transition-colors">
                      <XCircle size={16} /> Rejeter
                    </button>
                  </div>
                </div>
              ))}

              {currentData.length === 0 && (
                <div className="col-span-full text-center py-20 text-slate-400 bg-white rounded-2xl border border-dashed border-slate-200 font-medium">
                  Aucun événement ne correspond à vos critères.
                </div>
              )}

              {/* Vues simplifiées pour Publiés / Rejetés (Utilise aussi paginatedData) */}
              {activeTab === "published" && paginatedData.map((ev, i) => (
                <div key={i} className="bg-white rounded-xl p-5 shadow-sm border-l-4 border-green-400">
                  <h3 className="font-bold text-slate-800 text-sm mb-1 line-clamp-1">{ev.title}</h3>
                  <p className="text-xs text-slate-400">{ev.start_date} • {ev.source}</p>
                </div>
              ))}
              {activeTab === "rejected" && paginatedData.map((ev, i) => (
                <div key={i} className="bg-white rounded-xl p-5 shadow-sm border-l-4 border-slate-300 opacity-60">
                  <h3 className="font-bold text-slate-500 text-sm mb-1 line-clamp-1 line-through">{ev.title}</h3>
                  <p className="text-xs text-slate-400">{ev.source}</p>
                </div>
              ))}
            </div>

            {/* NOUVEAU : CONTRÔLES DE PAGINATION */}
            {totalPages > 1 && (
              <div className="flex justify-center items-center gap-6 mt-8 mb-4">
                <button 
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))} 
                  disabled={currentPage === 1} 
                  className="p-2.5 bg-white rounded-xl shadow-sm border border-slate-100 disabled:opacity-40 hover:text-[#4318FF] transition-colors"
                >
                  <ChevronLeft size={20} />
                </button>
                <span className="font-semibold text-sm text-slate-500">
                  Page {currentPage} sur {totalPages}
                </span>
                <button 
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} 
                  disabled={currentPage === totalPages} 
                  className="p-2.5 bg-white rounded-xl shadow-sm border border-slate-100 disabled:opacity-40 hover:text-[#4318FF] transition-colors"
                >
                  <ChevronRight size={20} />
                </button>
              </div>
            )}
          </div>
        )}
      </main>

      {/* --- SIDEBAR DROITE (Widgets & Calendrier) --- */}
      <aside className="w-80 bg-[#F8FAFC] border-l border-slate-200 flex-shrink-0 p-6 overflow-y-auto hidden lg:block">
        
        {renderCalendar()}

        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100">
          <h3 className="font-bold text-[#0F172A] mb-4">Vue d'ensemble</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm font-semibold mb-1">
                <span className="text-slate-500">Taux de publication</span>
                <span className="text-[#4318FF]">
                  {queue.length + published.length + rejected.length > 0 
                    ? Math.round((published.length / (queue.length + published.length + rejected.length)) * 100) 
                    : 0}%
                </span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2">
                <div className="bg-[#4318FF] h-2 rounded-full" style={{ width: `${queue.length + published.length + rejected.length > 0 ? (published.length / (queue.length + published.length + rejected.length)) * 100 : 0}%` }}></div>
              </div>
            </div>
            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <span className="text-sm font-medium text-slate-500">Volume Total Scrappé</span>
              <span className="text-lg font-bold text-[#0F172A]">{queue.length + published.length + rejected.length}</span>
            </div>
          </div>
        </div>
      </aside>

    </div>
  );
}