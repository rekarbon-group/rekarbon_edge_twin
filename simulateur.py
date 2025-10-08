import streamlit as st
if 'lang' not in st.session_state:
    st.session_state['lang'] = 'FR'

import pandas as pd
import time
import numpy as np 
from datetime import datetime
from fpdf import FPDF
from io import BytesIO
import altair as alt 
import io 
from collections import deque 
import locale 
import random # Ajout pour simuler des données aléatoires

# ================================
# CONFIGURATION DE LA PAGE STREAMLIT (DOIT ÊTRE LE PREMIER APPEL ST)
# ================================
st.set_page_config(
    page_title="Rekarbon Edge Twin – Démo Sécurisée",
    page_icon="https://rekarbon.com/favicon.ico",
    layout="wide",
)

# ==========================================================
# LOADER ET STYLES GLOBAUX
# ==========================================================

st.markdown("""
<style>
/* Styles pour l'animation du loader */
@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.04); opacity: 0.9; }
  100% { transform: scale(1); opacity: 1; }
}
@keyframes spin-slow {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
.loader {
  background: linear-gradient(90deg, #0f5132 0%, #198754 100%);
  color: white;
  border-radius: 12px;
  padding: 14px 18px;
  margin-top: 4px;
  box-shadow: 0 6px 18px rgba(0,0,0,0.18);
  animation: pulse 1.7s ease-in-out infinite;
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}
.loader .logo {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  animation: spin-slow 8s linear infinite;
  box-shadow: 0 0 0 2px rgba(255,255,255,0.2) inset;
}
.loader .text {
  font-weight: 700;
  letter-spacing: .2px;
}

/* Masquer le menu, header et footer par défaut (style deeptech propre) */
#MainMenu, header, footer {visibility: hidden;}

/* Style pour la fenêtre de log */
.log-box {
    height: 250px;
    background-color: #1c1c1c;
    color: #00FF00; /* Vert rétro pour l'effet console */
    font-family: monospace;
    padding: 10px;
    border-radius: 8px;
    overflow-y: scroll;
    font-size: 0.85rem;
    white-space: pre; /* Conserve les espaces */
}
</style>
""", unsafe_allow_html=True)

# ===================================================================
# CONFIGURATION GLOBALE ET SÉCURITÉ (CONSERVÉ DE VOTRE ZONE B)
# ===================================================================
SUPABASE_URL = None
SUPABASE_KEY = None

TEMP_NORMALE = 130.0
HUMIDITE_CIBLE = 12.0
VIBRATION_SEUIL_DEFAUT = 1.3 # Valeur par défaut avant l'initialisation du slider
SEED = 42 # Seed pour la reproductibilité de la démo

# ===================================================================
# I18N (INTERNATIONALISATION MINIMALE) - CONSERVÉ DE VOTRE ZONE B
# ===================================================================
I18N = {
    "FR": {
        "title": "Tableau de Bord de Contrôle Global - Rekarbon",
        "caption": "Démo publique — données simulées en local (aucun envoi réseau).",
        "menu_title": "MENU SIMULATIONS",
        "run_one": "▶️ Lancer une mesure manuelle",
        "run_series": "▶️ Lancer série",
        "reset_demo": "🔄 Réinitialiser la démo",
        "back": "⬅️ Retour à la Synthèse",
        "params": "⚙️ Paramètres (démo)",
        "vib_thr": "Seuil d’alerte vibration (g)",
        "run_sim": "▶️ Lancer la simulation",
        "choose_sim": "Choisissez une simulation à lancer :",
        "choose_state": "Choisissez un état pour le système :",
        "synth_title": "Synthèse & KPIs Clés",
        "sensor_sim_title": "Simulateur de Capteurs (Démo Edge)",
        "maint_sim_title": "Maintenance Prédictive",
        "log_sim_title": "Optimisation Logistique",
        "sargasses_title": "Valorisation Sargasses (Trio Produits)",
        "run_state_normal": "Normal",
        "run_state_alert": "Alerte",
        "biochar_scenario": "Biochar Marin (Séquestration Carbone)",
        "syngas_scenario": "Syngaz (Production d'Énergie)",
        "biohuile_scenario": "Bio-huile (Substitut Chimique)",
        "analyze": "ANALYSE",
        "report": "Rapport",
        "download": "Télécharger le PDF",
        "sarg_settings": "⚙️ Paramètres Sargasses",
        "sarg_tonnage_wet": "Tonnage humide (t)",
        "sarg_moisture": "Humidité (%) / Moisture",
        "sarg_yield_bch": "Rendement Biochar (t/t MS)",
        "sarg_yield_syg": "Rendement Syngaz (t/t MS)",
        "sarg_yield_bho": "Rendement Bio-huile (t/t MS)",
        "sarg_price_bch": "Prix Biochar (€/t)",
        "sarg_price_bho": "Prix Bio-huile (€/t)",
        "sarg_price_kwh": "Prix élec (€/kWh)",
        "sarg_kwh_per_t": "kWh par tonne Syngaz",
        "sarg_export": "⬇️ Exporter résultats (CSV)",
        "revenue_calc_title": "Calculateur de Revenus (Site Web)", # MIS À JOUR
    },
    "EN": {
        "title": "Rekarbon – Global Control Dashboard",
        "caption": "Public demo — simulated local data (no network transmission).",
        "menu_title": "SIMULATIONS MENU",
        "run_one": "▶️ Run manual measurement",
        "run_series": "▶️ Run series",
        "reset_demo": "🔄 Reset demo",
        "back": "⬅️ Back to Synthesis",
        "params": "⚙️ Parameters (demo)",
        "vib_thr": "Vibration Alert Threshold (g)",
        "run_sim": "▶️ Run simulation",
        "choose_sim": "Choose a simulation to run:",
        "choose_state": "Choose a system state:",
        "synth_title": "Synthesis & Key KPIs",
        "sensor_sim_title": "Sensor Simulator (Edge Demo)",
        "maint_sim_title": "Predictive Maintenance",
        "log_sim_title": "Logistics Optimization",
        "sargasses_title": "Sargassum Valorization (Product Trio)",
        "run_state_normal": "Normal",
        "run_state_alert": "Alert",
        "biochar_scenario": "Marine Biochar (Carbon Sequestration)",
        "syngas_scenario": "Syngas (Energy Production)",
        "biohuile_scenario": "Bio-oil (Chemical Substitute)",
        "analyze": "ANALYSIS",
        "report": "Report",
        "download": "Download PDF",
        "sarg_settings": "⚙️ Sargassum Settings",
        "sarg_tonnage_wet": "Wet Tonnage (t)",
        "sarg_moisture": "Moisture (%)",
        "sarg_yield_bch": "Biochar Yield (t/t DS)",
        "sarg_yield_syg": "Syngas Yield (t/t DS)",
        "sarg_yield_bho": "Bio-oil Yield (t/t DS)",
        "sarg_price_bch": "Biochar Price (€/t)",
        "sarg_price_bho": "Bio-oil Price (€/t)",
        "sarg_price_kwh": "Elec Price (€/kWh)",
        "sarg_kwh_per_t": "kWh per ton Syngas",
        "sarg_export": "⬇️ Export results (CSV)",
        "revenue_calc_title": "Revenue Calculator (Website)", # MIS À JOUR
    },
}

def T(lang, key_or_fr_text, en_text=None): 
    """
    Helper function for translation. Accepts (lang, key) or (lang, FR_text, EN_text) for inline.
    """
    # Case 1: Inline translation (3 arguments: T(lang, FR_text, EN_text))
    if en_text is not None:
        return en_text if lang == "EN" else key_or_fr_text
    
    # Case 2: Standard dictionary lookup (2 arguments: T(lang, key))
    lang_dict = I18N.get(lang, I18N["FR"]) 
    return lang_dict.get(key_or_fr_text, key_or_fr_text)


# =================================================
# SÉLECTEUR DE LANGUE & INITIALISATION
# =================================================

# Utiliser st.session_state pour maintenir la langue choisie
if 'lang' not in st.session_state:
    st.session_state['lang'] = 'FR'

# Place le sélecteur de langue en haut de la barre latérale
st.sidebar.markdown('**🌍 Langue | Language**')
st.session_state['lang'] = st.sidebar.radio(
    "", 
    options=['FR', 'EN'], 
    index=0, 
    key='lang_selector_new',
    horizontal=True,
    label_visibility="collapsed"
)
lang = st.session_state['lang']
st.sidebar.markdown("---")

# Texte bilingue pour le loader
_txt = T(lang, "choose_state") # Utilisation d'un texte générique pour le loader.

# HTML du loader
st.markdown(f"""
<div class="loader">
  <img class="logo" alt="Rekarbon" src="https://www.rekarbon.com/favicon.ico">
  <div class="text">{T(lang, "synth_title")}</div>
</div>
""", unsafe_allow_html=True)

# Petite pause pour l'effet "chargement"
time.sleep(1.8)

# Message de prêt bilingue
_ready = "✅ Système prêt — exécution locale sécurisée." if lang == "FR" else "✅ System ready — secure local execution mode."
st.success(_ready)
st.markdown("---")


# ==========================================================
# BANNIÈRE TECHNIQUE (Styles et HTML fusionnés)
# ==========================================================

# Préparation des chaînes traduites pour injection HTML
demo_title = T(lang, "Démonstration <b>Rekarbon Edge Twin</b>", "<b>Rekarbon Edge Twin</b> Demonstration")
arch_main = T(lang, "Propulsé par une architecture Dual Raspberry Pi 5 et 2x Pico Controllers", "Powered by Dual Raspberry Pi 5 and 2x Pico Controllers architecture")
arch_details = T(lang, "(Architecture entièrement déconnectée et auto-synchronisée)", "(Fully offline and self-synchronizing architecture)")


st.markdown(f"""
<style>
@keyframes fadeIn {{
  from {{ opacity: 0; transform: translateY(10px); }}
  to   {{ transform: translateY(0); }}
}}

/* Couleurs par défaut (mode clair) */
:root {{
  --banner-bg: linear-gradient(90deg, #0f5132 0%, #198754 100%);
  --banner-fg: #ffffff;
  --banner-shadow: 0 6px 18px rgba(0,0,0,.25);
}}

/* Auto dark mode */
@media (prefers-color-scheme: dark) {{
  :root {{
    --banner-bg: linear-gradient(90deg, #0b3b25 0%, #146c43 100%);
    --banner-fg: #eaf7ef;
    --banner-shadow: 0 10px 24px rgba(0,0,0,.45);
  }}
}}

.banner {{
  background: var(--banner-bg);
  color: var(--banner-fg);
  padding: 18px 22px;
  border-radius: 14px;
  margin-top: 22px;
  text-align: center;
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  box-shadow: var(--banner-shadow);
  animation: fadeIn 1.2s ease-out;
  position: relative;
  overflow: hidden;
}}
.banner h3 {{
  margin: 0;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: 1.15rem;
}}
.banner img {{
  width: 30px;
  height: 30px;
  vertical-align: middle;
  filter: drop-shadow(0 2px 2px rgba(0,0,0,0.3));
}}
.banner p {{
  margin: 4px 0 0 0;
  font-size: .9rem;
  opacity: .95;
}}
.badge {{
  position: absolute;
  top: 12px;
  right: 16px;
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.25);
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 0.75rem;
  letter-spacing: 0.5px;
  font-weight: 600;
  color: var(--banner-fg);
  backdrop-filter: blur(4px);
}}
</style>

<div class="banner">
  <div class="badge">🟢 EDGE NATIVE MODE</div>
  <h3>
    <img src="https://upload.wikimedia.org/wikipedia/commons/c/cb/Raspberry_Pi_Logo.svg" alt="Raspberry Pi Logo">
    ⚙️ {demo_title}
  </h3>
  <p>🍃 <b>{arch_main}</b></p>
  <p class="mt-2 text-xs opacity-80"><i>{arch_details}</i></p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# =================================================
# FONCTIONS DE LOGIQUE ET FORMATAGE
# =================================================

# FIX C: Configuration locale pour le format monétaire FR
try:
    locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'fra_FRA')
    except locale.Error:
        pass 

def eur(x): 
    """Formate la valeur en devise française avec fallback manuel."""
    try: 
        # Utiliser un format avec séparateur d'espace pour les milliers
        return locale.currency(x, grouping=True, symbol=True).replace(',', ' ').replace('.', ',')
    except Exception: 
        # Fallback manuel si locale.setlocale échoue sur le serveur
        return f"{x:,.0f} €".replace(',', ' ').replace('.', ',')

# --- Bip de démarrage (une seule fois par session) ---
if "boot_beep_done" not in st.session_state:
    st.session_state.boot_beep_done = False

# La fonction est définie une seule fois
def _play_boot_beep():
    st.markdown("""
<script>
(function(){
  try{
    const ctx = new (window.AudioContext || window.webkitAudioContext)();

    function beep(freq, duration, delay){
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.type = "sine";
      o.frequency.value = freq;

      // envelope (fade in/out to avoid clicks)
      g.gain.setValueAtTime(0.0001, ctx.currentTime + delay);
      g.gain.exponentialRampToValueAtTime(0.08,  ctx.currentTime + delay + 0.01);
      g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + delay + duration);

      o.connect(g); g.connect(ctx.destination);
      o.start(ctx.currentTime + delay);
      o.stop(ctx.currentTime + delay + duration);
    }

    // Double bip : "boot" puis "sync"
    beep(660, 0.15, 0.00);  // premier bip (boot)
    beep(880, 0.18, 0.25);  // second bip (sync)
  } catch(e){}
})();
</script>
""", unsafe_allow_html=True)

# =================================================
# BARRE LATÉRALE - PARAMÈTRES DE SIMULATION
# =================================================
# ATTENTION: Cette section ne s'affiche que lorsque l'onglet 'Analyse Edge' est sélectionné dans la ZONE B
st.sidebar.title(T(lang, "params")) # Utilise le titre "Paramètres (démo)"
st.sidebar.markdown("---")

st.sidebar.subheader(T(lang, "choose_sim")) # Titre générique pour l'espace vide

# La logique de la barre latérale pour l'analyse Edge est insérée dans la fonction de routage pour éviter les conflits
# Nous allons insérer les paramètres d'analyse Edge dans la section principale pour les rendre accessibles.

# La barre latérale Menu est gérée par votre ZONE B (lignes 900+)

# =================================================
# LOGIQUE DE SIMULATION DE L'ANALYSE ÉNERGÉTIQUE
# =================================================

# PARAMÈTRES PHYSIQUES INTERNES (Exemples basés sur RPi 5/Pico, ajustables)
NOMINAL_POWER_W = 15.0 
HOURS_PER_DAY = 24

# RENDEMENTS ET PRIX DE BASE POUR LE CALCULATEUR DE REVENUS
REVENUES_CONFIG = {
    # yield_bch: Rendement Biochar (t Biochar / t Matière Sèche)
    # moisture: Humidité de la biomasse brute (0.0 à 1.0)
    "manure": {"yield_bch": 0.35, "moisture": 0.80}, # 80% humidité
    "sargassum": {"yield_bch": 0.40, "moisture": 0.85}, # 85% humidité
    "wood": {"yield_bch": 0.30, "moisture": 0.50}, # 50% humidité
    # Facteurs de séquestration CO2 (tonnes CO2e par tonne de Biochar)
    "co2_factor": 2.75, 
    # Prix
    "price_biochar": 450, # €/tonne
    "price_credit_premium": 300, # €/tCO2e (MRV Traceable)
    "price_credit_standard": 60,  # €/tCO2e (Non-traceable)
}


def calculate_performance(duration_days, usage_percent, factor_gco2, cost_eur_kwh):
    """Calcule les émissions totales de CO2 et le coût total de fonctionnement."""
    actual_hours = duration_days * HOURS_PER_DAY * (usage_percent / 100)
    total_kwh = (NOMINAL_POWER_W * actual_hours) / 1000
    total_co2_kg = (total_kwh * factor_gco2) / 1000
    total_cost_eur = total_kwh * cost_eur_kwh
    return {'total_kwh': total_kwh, 'total_co2_kg': total_co2_kg, 'total_cost_eur': total_cost_eur}

def generate_time_series_data(duration_days, usage_percent, factor_gco2, cost_eur_kwh):
    """Génère un DataFrame pandas avec l'accumulation jour par jour."""
    data = []
    daily_kwh = (NOMINAL_POWER_W * HOURS_PER_DAY * (usage_percent / 100)) / 1000
    daily_co2_kg = (daily_kwh * factor_gco2) / 1000
    daily_cost_eur = daily_kwh * cost_eur_kwh
    cumulative_co2 = 0
    cumulative_cost = 0
    for day in range(1, duration_days + 1):
        cumulative_co2 += daily_co2_kg
        cumulative_cost += daily_cost_eur
        data.append({'Jour': day, 'Valeur': cumulative_co2, 'Metric': T(lang, 'Impact Carbone (kg CO₂e)', 'Carbon Impact (kg CO₂e)')})
        data.append({'Jour': day, 'Valeur': cumulative_cost, 'Metric': T(lang, 'Coût (€)', 'Cost (€)')})
    return pd.DataFrame(data)

# =================================================
# NOUVELLE FONCTION DE SIMULATION ÉNERGÉTIQUE (Edge Analysis)
# =================================================
def simuler_analyse_energetique(lang):
    """Affiche la simulation d'analyse énergétique que nous avons construite."""
    st.header(T(lang, "Analyse de la performance énergétique Rekarbon", "Rekarbon Energy Performance Analysis"))
    
    # NOUVELLE DESCRIPTION DE L'ARCHITECTURE MATÉRIELLE (CORRIGÉE)
    architecture_description = T(
        lang, 
        "Cette **simulation n'est pas une démo logicielle**. Elle reproduit notre architecture cible : elle utilise **deux Raspberry Pi 5** pour le traitement distribué des données brutes, fournies par deux Picos qui simulent les capteurs et actionneurs physiques. L'ensemble est visible sur Streamlit. Nous avons ainsi validé l'ensemble de la chaîne, du Edge à l'interface, de manière **frugale et rapide**.",
        "This **simulation is not just a software demo**. It replicates our target architecture: it uses **two Raspberry Pi 5s** for distributed processing of raw data, supplied by two Picos simulating physical sensors and actuators. The whole chain is visualized on Streamlit. This allowed us to validate the entire chain, from the Edge to the interface, in a **frugal and rapid** manner."
    )
    st.info(architecture_description)

    st.markdown("---")

    # 1. PARAMÈTRES DE LA BARRE LATÉRALE (DÉPLACÉS ICI POUR L'ACCÈS LOCAL)
    # L'affichage de ces paramètres doit être inclus ici pour l'exécution locale.
    
    st.sidebar.subheader(T(lang, "Twin Numérique et Période", "Digital Twin & Period"))

    simulation_duration = st.sidebar.slider(
        T(lang, "Durée de la simulation (jours)", "Simulation Duration (days)"), 
        min_value=1, max_value=365, value=30, step=1, key='sim_duration_an'
    )
    utilization_rate = st.sidebar.slider(
        T(lang, "Taux d'utilisation de l'équipement (%)", "Equipment Utilization Rate (%)"), 
        min_value=0, max_value=100, value=80, step=5, key='util_rate_an'
    )
    st.sidebar.markdown("---")

    st.sidebar.subheader(T(lang, "Émissions et Coûts", "Emissions & Costs"))

    emission_factor = st.sidebar.number_input(
        T(lang, "Facteur d'émission électrique ($gCO_{2}e/kWh$)", "Electricity Emission Factor ($gCO_{2}e/kWh$)"), 
        min_value=10, max_value=1000, value=50, step=10, key='emiss_factor_an',
        help=T(lang, "Facteur carbone de l'électricité (ex: 50 pour la France, 450 pour l'Allemagne).",
               "Carbon factor of electricity (e.g., 50 for France, 450 for Germany).")
    )

    electricity_cost = st.sidebar.number_input(
        T(lang, "Coût de l'électricité ($€/kWh$)", "Electricity Cost ($€/kWh$)"), 
        min_value=0.01, max_value=1.0, value=0.15, step=0.01, format="%.2f", key='cost_an',
        help=T(lang, "Coût moyen de l'électricité pour le calcul des économies.",
               "Average cost of electricity for savings calculation.")
    )
    st.sidebar.markdown("---")


    # Exécuter la simulation et générer les données de la série temporelle
    results = calculate_performance(simulation_duration, utilization_rate, emission_factor, electricity_cost)
    chart_data = generate_time_series_data(simulation_duration, utilization_rate, emission_factor, electricity_cost)


    # 2. AFFICHAGE DES RÉSULTATS (KPIs)
    col1, col2, col3 = st.columns(3)
    col1.metric(label=T(lang, "Consommation totale", "Total Consumption"), value=f"{results['total_kwh']:,.1f} kWh", delta_color="off")
    col2.metric(label=T(lang, "Impact Carbone total", "Total Carbon Impact"), value=f"{results['total_co2_kg']:,.2f} kg CO₂e", delta_color="inverse")
    col3.metric(label=T(lang, "Coût total estimé", "Estimated Total Cost"), value=eur(results['total_cost_eur']), delta_color="off")
    st.markdown("---")


    # 3. VISUALISATION DES DONNÉES CUMULÉES (Altair)
    st.subheader(T(lang, "Évolution cumulée des coûts et des émissions", "Cumulative Evolution of Costs and Emissions"))
    COLOR_CO2 = '#198754' 
    COLOR_COST = '#FF6347' 
    
    chart = alt.Chart(chart_data).mark_line(point=True).encode(
        x=alt.X('Jour:Q', title=T(lang, "Jour de la simulation", "Simulation Day")),
        y=alt.Y('Valeur:Q', title=T(lang, "Valeur Cumulée", "Cumulative Value")),
        color=alt.Color('Metric:N', legend=alt.Legend(title=T(lang, "Métrique", "Metric")),
                        scale=alt.Scale(domain=[T(lang, 'Impact Carbone (kg CO₂e)', 'Carbon Impact (kg CO₂e)'), 
                                                T(lang, 'Coût (€)', 'Cost (€)')],
                                        range=[COLOR_CO2, COLOR_COST])),
        tooltip=[alt.Tooltip('Jour:Q', title=T(lang, 'Jour', 'Day')),
                 alt.Tooltip('Metric:N', title=T(lang, 'Métrique', 'Metric')),
                 alt.Tooltip('Valeur:Q', title=T(lang, 'Valeur', 'Value'), format=".2f")]
    ).interactive() 

    st.altair_chart(chart, use_container_width=True)


    # 4. EXPORTATION DES RÉSULTATS (PDF)
    st.subheader(T(lang, "Exporter et imprimer l'analyse", "Export and Print Analysis"))
    st.markdown("---")
    
    # La fonction create_pdf_report est désormais définie ci-dessous

    # Génération du fichier PDF et bouton de téléchargement
    # pdf_file = create_pdf_report(results, chart_data, lang) # Non défini dans ce bloc, mais supposé être dans le fichier complet

    # st.download_button(
    #     label=T(lang, "⬇️ Télécharger le Rapport PDF", "⬇️ Download PDF Report"),
    #     data=pdf_file,
    #     file_name=f"Rekarbon_EdgeTwin_Rapport_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
    #     mime="application/octet-stream",
    #     help=T(lang, "Génère un rapport téléchargeable des résultats de la simulation au format PDF.",
    #             "Generates a downloadable PDF report of the simulation results.")
    # )

    # 5. MODULE DE LOGS EN TEMPS RÉEL
    st.subheader(T(lang, "Flux de données temps réel (Edge Log)", "Real-time Data Stream (Edge Log)"))
    st.markdown("---")

    MAX_LOG_LINES = 15
    if 'log_history' not in st.session_state:
        st.session_state.log_history = deque(maxlen=MAX_LOG_LINES)

    # Placeholder pour la boîte de logs (permet la mise à jour sans recharger toute la page)
    log_placeholder = st.empty()

    def simulate_edge_data(duration_seconds=10):
        """Simule l'arrivée de logs de données Edge pour une courte période."""
        start_time = time.time()
        
        if not st.session_state.get('log_running', False):
            st.session_state.log_running = True
            
            while time.time() - start_time < duration_seconds:
                current_time_str = datetime.now().strftime("[%H:%M:%S]")
                power = round(random.uniform(14.5, 15.5), 2)
                temp = round(random.uniform(40.0, 45.0), 1)
                status = random.choice(["OK", "SYNC", "MEASURE", "COMPUTE"])
                
                log_line = f"{current_time_str} [P{random.randint(1,2)}] {status:<7} | Power: {power:.2f}W | Temp: {temp:.1f}°C"
                
                st.session_state.log_history.appendleft(log_line) 
                log_content = "\n".join(st.session_state.log_history)
                
                log_placeholder.markdown(f'<div class="log-box">{log_content}</div>', unsafe_allow_html=True)
                time.sleep(0.5) 
            
            st.session_state.log_running = False
            
            log_placeholder.markdown(f'<div class="log-box">{log_content}\n{datetime.now().strftime("[%H:%M:%S]")} [System] Simulation des logs terminée.</div>', unsafe_allow_html=True)


    if st.button(T(lang, "▶️ Démarrer le Flux de Données (10s)", "▶️ Start Data Stream (10s)")):
        simulate_edge_data(duration_seconds=10)

# =================================================
# NOUVELLE FONCTION : LIEN VERS CALCULATRICE EXTERNE
# =================================================

def simuler_revenue_link(lang):
    """
    Crée un lien cliquable vers la calculatrice de revenus externe.
    """
    st.header(T(lang, "Calculateur de Revenus (Valorisation Biochar)", "Revenue Calculator (Biochar Valorization)"))
    st.info(T(lang, "Pour une estimation détaillée du revenu potentiel issu de la transformation des déchets en biochar et crédits carbone, veuillez utiliser notre outil en ligne.",
                    "For a detailed estimation of potential revenue from transforming waste into biochar and carbon credits, please use our online tool."))
    st.markdown("---")
    
    # Bouton cliquable qui ouvre le lien dans un nouvel onglet
    link_text = T(lang, "Calculer mon Revenu Potentiel", "Calculate My Potential Revenue")

    st.markdown(f"""
    <div style='text-align:center; margin-top: 30px;'>
        <a href="https://www.rekarbon.com/calculator" target="_blank" rel="noopener" style='
            background-color: #198754;
            color: white;
            padding: 12px 30px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease-in-out;
            display: inline-block;
        '>
        {link_text} 🔗
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")


# ===================================================================
# FONCTIONS UTILITAIRES POUR PDF ET NAVIGATION (ADAPTÉES DE VOTRE ZONE B)
# ... (La suite des fonctions est conservée) ...
# ===================================================================

# J'ai omis ici la répétition des fonctions (create_pdf_report, back_to_synthesis_button, generate_pdf, etc.)
# qui sont conservées dans le bloc complet du Canvas.

# ===================================================================
# FONCTIONS UTILITAIRES POUR PDF ET NAVIGATION (ADAPTÉES DE VOTRE ZONE B)
# ===================================================================
def create_pdf_report(results, chart_data, lang):
    """Crée un rapport PDF FPDF avec les résultats de la simulation (Fusionné avec la logique eur)."""
    
    pdf = FPDF()
    pdf.add_page()
    
    # Définir la police pour supporter les accents
    pdf.set_font("Arial", size=12)
    
    # En-tête du rapport
    title_fr = "Rapport d'Analyse Rekarbon Edge Twin"
    title_en = "Rekarbon Edge Twin Analysis Report"
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, T(lang, title_fr, title_en), 0, 1, 'C')
    pdf.ln(5)

    # Date de la simulation
    date_label = T(lang, "Date de la simulation : ", "Simulation Date: ")
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 5, date_label + datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0, 1, 'L')
    pdf.ln(5)

    # Section 1: Paramètres
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, T(lang, "Paramètres de la Simulation", "Simulation Parameters"), 0, 1, 'L')
    pdf.set_font("Arial", size=10)
    
    # Récupération des valeurs nécessaires pour l'affichage (depuis les dernières valeurs globales du script)
    # Note: On utilise ici les valeurs directement sans les passer en paramètres, car elles sont globales dans le script Streamlit.
    try:
        pdf.cell(0, 5, T(lang, f"- Durée: {st.session_state['sim_duration_an']} jours", f"- Duration: {st.session_state['sim_duration_an']} days"), 0, 1)
        pdf.cell(0, 5, T(lang, f"- Utilisation: {st.session_state['util_rate_an']}%", f"- Utilization: {st.session_state['util_rate_an']}%"), 0, 1)
        pdf.cell(0, 5, T(lang, f"- Facteur Carbone: {st.session_state['emiss_factor_an']} gCO2e/kWh", f"- Carbon Factor: {st.session_state['emiss_factor_an']} gCO2e/kWh"), 0, 1)
        pdf.cell(0, 5, T(lang, f"- Coût Électricité: {eur(st.session_state['cost_an'])}/kWh", f"- Electricity Cost: {eur(st.session_state['cost_an'])}/kWh"), 0, 1)
    except KeyError:
         # Fallback au cas où l'utilisateur n'a pas encore interagi avec le slider
        pdf.cell(0, 5, T(lang, "- Paramètres par défaut chargés.", "- Default parameters loaded."), 0, 1)
    pdf.ln(8)

    # Section 2: Résultats Clés (KPIs)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, T(lang, "Résultats Clés", "Key Results"), 0, 1, 'L')
    pdf.set_font("Arial", size=10)
    
    # KPI 1
    pdf.cell(70, 6, T(lang, "Consommation Totale :", "Total Consumption:"), 0, 0, 'L')
    pdf.cell(0, 6, f"{results['total_kwh']:,.1f} kWh", 0, 1, 'L')
    
    # KPI 2
    pdf.cell(70, 6, T(lang, "Impact Carbone Total :", "Total Carbon Impact:"), 0, 0, 'L')
    pdf.cell(0, 6, f"{results['total_co2_kg']:,.2f} kg CO₂e", 0, 1, 'L')
    
    # KPI 3
    pdf.cell(70, 6, T(lang, "Coût Total Estimé :", "Estimated Total Cost:"), 0, 0, 'L')
    pdf.cell(0, 6, eur(results['total_cost_eur']), 0, 1, 'L')
    
    pdf.ln(8)
    
    # Section 3: Données Brutes (Extrait)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, T(lang, "Extrait des Données (Jour 1 à 7)", "Data Sample (Day 1 to 7)"), 0, 1, 'L')
    pdf.set_font("Arial", size=8)

    # Préparation d'un extrait de DataFrame pour le PDF
    df_pivot = chart_data.pivot_table(index='Jour', columns='Metric', values='Valeur').reset_index()
    df_display = df_pivot.head(7)

    # Titres des colonnes du tableau
    col_width = [25, 45, 45]
    
    # Définition des titres pour le tableau
    headers = [T(lang, 'Jour', 'Day'), T(lang, 'Impact Carbone (kg CO₂e)', 'Carbon Impact (kg CO₂e)'), T(lang, 'Coût (€)', 'Cost (€)')]
    
    # Affichage des titres
    pdf.set_fill_color(220, 220, 220)
    for i, header in enumerate(headers):
        pdf.cell(col_width[i], 7, header, 1, 0, 'C', 1)
    pdf.ln()

    # Affichage des données
    pdf.set_font("Arial", size=8)
    for index, row in df_display.iterrows():
        pdf.cell(col_width[0], 6, str(int(row['Jour'])), 1, 0, 'C')
        pdf.cell(col_width[1], 6, f"{row[headers[1]]:.2f}", 1, 0, 'R')
        pdf.cell(col_width[2], 6, f"{row[headers[2]]:.2f} €", 1, 1, 'R')
        
    pdf.ln(10)
    
    # Note de bas de page
    pdf.set_font("Arial", 'I', 8)
    pdf.multi_cell(0, 4, T(lang, "Ce rapport est basé sur les paramètres configurés dans la démo Rekarbon Edge Twin.", 
                     "This report is based on the parameters configured in the Rekarbon Edge Twin demo."), 0, 'C')

    # Conversion en bytes
    pdf_output = pdf.output(dest='S').encode('latin-1', 'replace') # Utilisation de replace pour la robustesse
    return pdf_output

def back_to_synthesis_button(lang, key):
    """Génère le bouton de retour à la synthèse et déclenche un rerun."""
    st.markdown("---")
    if st.button(T(lang, "back"), key=key):
        st.session_state["_return_to_synth"] = True
        st.rerun()

def generate_pdf(simulation_title, report_data):
    """Génère un rapport PDF FPDF plus générique (pour les autres simulations)."""
    pdf = FPDF()
    pdf.add_page()
    
    # Helper pour encoder de manière sûre en latin-1 pour le PDF
    def _safe_txt(x):
        s = str(x).replace("•", "-") 
        s = s.replace("€", "EUR ") 
        try:
            s.encode("latin-1")
            return s
        except UnicodeEncodeError:
            return s.encode("latin-1", "replace").decode("latin-1")

    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, _safe_txt('Rekarbon - Rapport de Simulation Confidentiel'), 0, 1, 'C')
    pdf.set_font("Helvetica", '', 8)
    pdf.cell(0, 10, _safe_txt(f"Généré le : {datetime.now():%d/%m/%Y %H:%M:%S}"), 0, 1, 'C')
    pdf.ln(10)
    
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, _safe_txt(simulation_title), 0, 1, 'L')
    pdf.set_font("Helvetica", '', 11)
    
    for field, value in report_data.items():
        pdf.set_font("Helvetica", 'B', 10)
        pdf.multi_cell(0, 8, f"- {_safe_txt(field)}:")
        pdf.set_font("Helvetica", '', 10)
        if isinstance(value, list):
            for item in value:
                pdf.multi_cell(0, 6, f"  - {_safe_txt(item)}") 
        else:
            pdf.multi_cell(0, 8, f"  {_safe_txt(value)}")
            
    pdf_output = pdf.output(dest='S').encode('latin-1', 'replace') 
    return BytesIO(pdf_output)


# ===================================================================
# FONCTION DE SYNTHÈSE (PAGE D'ACCUEIL) - CONSERVÉE DE VOTRE ZONE B
# ===================================================================
def simuler_tableau_de_bord_kpis(lang):
    # Traductions minimales pour les titres
    if lang == "FR":
        st.subheader("📊 Tableau de Bord de Synthèse : KPIs Clés (Edge Twin)")
        st.info("Cette vue consolide les indicateurs critiques générés par les simulations d'IA et de traçabilité.")
        kpi_maint_title = "⚙️ Maintenance & Production"
        kpi_log_title = "🚚 Logistique & Stock"
        kpi_carb_title = "🌳 Carbone & Finance"
    else:
        st.subheader("📊 Synthesis Dashboard: Key KPIs (Edge Twin)")
        st.info("This view consolidates critical indicators generated by IA and traceability simulations.")
        kpi_maint_title = "⚙️ Maintenance & Production"
        kpi_log_title = "🚚 Logistics & Inventory"
        kpi_carb_title = "🌳 Carbon & Finance"

    
    # Données statiques représentant des résultats clés
    kpi_data = {
        T(lang, "maint_sim_title"): {
            "Statut critique": "SAFE (99% de fiabilité)",
            "Économies évitées (annuel)": eur(450000),
            "Dernière alerte": "Aucune (il y a 8 jours)"
        },
        T(lang, "log_sim_title"): {
            "Déficit critique (Bio-huile)": "0 tonne",
            "Taux de rupture évité": "97%",
            "Économie carburant (mois)": eur(8500)
        },
        "Reforestation & Carbone": {
            "CO2 séquestré certifié (annuel)": "14,500 tonnes",
            "Valorisation Tokens REKAR": eur(507500),
            "Tokens émis total": "42,000 REKAR"
        }
    }
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"### {kpi_maint_title}")
        st.metric("Fiabilité Machine 01", "99.8%", "+0.5%")
        st.metric("Temps d'Arrêt Imprévu", "0 h", "Cible Atteinte")
        
    with col2:
        st.markdown(f"### {kpi_log_title}")
        st.metric("Stock Critique (J-7)", "0 Alerte", "Risque évité")
        st.metric("Optimisation d'Itinéraire", "89%", "+3%")
    
    with col3:
        st.markdown(f"### {kpi_carb_title}")
        st.metric("Crédits Carbone Certifiés", "14,500 t", "Valorisé")
        st.metric("Tokens REKAR en circulation", "42,000 REKAR", "Stable")
    
    st.markdown("---")
    st.markdown("#### Détails Opérationnels" if lang == "FR" else "#### Operational Details")
    st.json(kpi_data)


# ===================================================================
# NOUVELLE FONCTION DE SIMULATION INTERACTIVE (DÉMO EDGE) - CONSERVÉE DE VOTRE ZONE B
# ===================================================================
def simuler_capteurs_safe_interactive(auto_run=False, seuil_alerte_defaut=VIBRATION_SEUIL_DEFAUT, lang="FR"):
    """
    Simulateur de Capteurs — version SAFE & interactive.
    Injecte des données de capteurs localement avec alerte de vibration.
    """
    # Initialisation du RNG pour la reproductibilité
    if SEED is not None and "rng_seeded" not in st.session_state:
        np.random.seed(SEED)
        st.session_state["rng_seeded"] = True

    # Accès au seuil sécurisé (on utilise le seuil de la session)
    seuil = float(st.session_state.get("seuil_vib", seuil_alerte_defaut))

    # Traductions via helper T()
    info_msg = "Mode démo : Aucune requête réseau externe. Les mesures sont simulées localement (Edge Native) et sont manipulables. Le graphique peut afficher une anomalie." if lang == "FR" else "Demo mode: No external network requests. Measures are locally simulated (Edge Native) and interactive. The graph may show an anomaly."
    title_msg = "🧪 Simulation : Données Capteurs (Démonstration Edge Sécurisée)" if lang == "FR" else "🧪 Sensor Data Simulation (Secure Edge Demo)"
    
    st.subheader(title_msg)
    st.info(info_msg)

    # ----------------- State -----------------
    if "sim_df" not in st.session_state:
        st.session_state.sim_df = pd.DataFrame(columns=["ts","Température","Vibration","Courant"])
    # FIX 5: Utilisation de deque pour des performances de log optimales
    if "log_lines" not in st.session_state:
        st.session_state.log_lines = deque(maxlen=200)
    if "local_auto_demo_done" not in st.session_state:
        st.session_state.local_auto_demo_done = False


    def log(msg):
        t = time.strftime("%H:%M:%S")
        st.session_state.log_lines.append(f"[{t}] {msg}")

    # ----------------- Simulation primitives -----------------
    def sample_point_with_alert(force_alert=False):
        # 5% de chance d'injecter une alerte (sauf si forcé)
        is_alert = force_alert or (np.random.rand() < 0.05)
        
        if is_alert:
            # Injecte une vibration anormale
            vibration = round(seuil + np.random.randn() * 0.3, 3)
            temp = round(65 + np.random.randn() * 2.0, 2)
            current = round(2.5 + np.random.randn() * 0.3, 3)
            log("🚨 Alerte générée : Vibration anormale injectée.")
        else:
            # Fonctionnement normal
            vibration = round(0.9 + abs(np.random.randn() * 0.05), 3)
            temp = round(60 + np.random.randn() * 0.4, 2)
            current = round(2.0 + np.random.randn() * 0.08, 3)

        return {
            "ts": time.strftime("%H:%M:%S"),
            "Température": temp,
            "Vibration": vibration,
            "Courant": current
        }

    def append_point(row):
        st.session_state.sim_df = pd.concat([st.session_state.sim_df, pd.DataFrame([row])], ignore_index=True).tail(500)

    # ----------------- Auto-demo (lancement automatique) -----------------
    if auto_run and not st.session_state.local_auto_demo_done:
        st.session_state.local_auto_demo_done = True
        log("Auto-démo automatique initialisée au chargement.")
        with st.spinner("Démarrage automatique de la simulation (mode démo)..."):
            # Lance 28 points normaux et 2 points d'alerte pour commencer
            for i in range(30):
                r = sample_point_with_alert(force_alert=(i in [20, 25]))
                append_point(r)
                time.sleep(0.06)
        st.success("Auto-démo exécutée (mode démo) : Données initiales injectées." if lang=="FR" else "Auto-demo executed (demo mode): Initial data injected.")
        log("Auto-démo exécutée.")


    # ----------------- UI Controls -----------------
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1.5,1.2,1])

    with col_ctrl1:
        # Ajout de clés uniques + i18n
        if st.button(T(lang, "run_one"), key="capteurs_run_one"):
            row = sample_point_with_alert()
            append_point(row)
            log("Mesure unique simulée ajoutée.")
            if row['Vibration'] >= seuil:
                 st.error("ALERTE : Anomalie de vibration détectée !" if lang=="FR" else "ALERT: Vibration anomaly detected!")
            else:
                 st.success("Mesure simulée ajoutée (mode démo)." if lang=="FR" else "Simulated measurement added (demo mode).")

    with col_ctrl2:
        if 'n_series' not in st.session_state:
             st.session_state.n_series = 20

        # i18n
        n_series = st.number_input(
            "Nombre de mesures (série)" if lang=="FR" else "Number of measurements (series)", 
            min_value=1, max_value=200, value=st.session_state.n_series, step=1, key="n_series_input"
        )
        st.session_state.n_series = n_series 

        # Ajout de clés uniques + i18n
        if st.button(T(lang, "run_series"), key="capteurs_run_series"):
            log(f"Démarrage série de {n_series} mesures.")
            with st.spinner("Génération de la série..." if lang=="FR" else "Generating series..."):
                alert_count = 0
                # Hard cap pour la fluidité sur Streamlit Cloud
                for _ in range(min(int(n_series), 120)): 
                    r = sample_point_with_alert()
                    append_point(r)
                    if r['Vibration'] >= seuil:
                        alert_count += 1
                    time.sleep(0.05) # Réduit le sleep pour la fluidité
            st.success(f"Série de {min(int(n_series), 120)} mesures générée. ({alert_count} alertes simulées)")
            log(f"Série de {min(int(n_series), 120)} mesures simulée.")

    with col_ctrl3:
        # Ajout de clés uniques + i18n
        if st.button(T(lang, "reset_demo"), key="capteurs_reset"):
            st.session_state.sim_df = st.session_state.sim_df.iloc[0:0]
            st.session_state.local_auto_demo_done = False 
            st.success("Démo capteurs réinitialisée." if lang=="FR" else "Sensor demo reset.")
            log("Démo capteurs réinitialisée manuellement.")

    st.markdown("---")

    # Petits KPI "toujours visibles"
    k1, k2, k3 = st.columns(3)
    if not st.session_state.sim_df.empty:
        last = st.session_state.sim_df.iloc[-1]
        k1.metric("Température (°C)", f"{last['Température']:.2f}")
        k2.metric("Vibration (g)", f"{last['Vibration']:.3f}")
        k3.metric("Courant (A)", f"{last['Courant']:.3f}")
    else:
        k1.metric("Température (°C)", "—")
        k2.metric("Vibration (g)", "—")
        k3.metric("Courant (A)", "—")

    # ----------------- Visualisations -----------------
    st.markdown("### 📈 Graphique temps réel (données simulées)" if lang=="FR" else "### 📈 Real-time chart (simulated data)")
    
    if not st.session_state.sim_df.empty:
        df_chart = st.session_state.sim_df.copy()
        
        # Micro-perf & robustesse (conversion sûre des colonnes)
        for c in ["Température","Vibration","Courant"]:
             df_chart[c] = pd.to_numeric(df_chart[c], errors="coerce")
        
        # FIX 3: Robustesse NaN: Drop NaN and reset index for Altair numerical X-axis
        dfc = df_chart.dropna(subset=["Vibration"]).reset_index(drop=True)
        
        # FIX 6: Garde-fou avant de dessiner les métriques et le graphique
        if dfc.empty:
            st.info("Pas encore de mesures utilisables." if lang=="FR" else "No usable measurements yet.")
        else:
            dfc["idx"] = np.arange(len(dfc)) # index croissant
            
            # Ne garder que 60 points pour le graphique
            if len(dfc) > 60:
                dfc = dfc.tail(60)
                
            line = alt.Chart(dfc).mark_line().encode(
                x=alt.X("idx:Q", title="Échantillon" if lang=="FR" else "Sample"), 
                # FIX 4: Ajout de nice=True pour l'échelle
                y=alt.Y("Vibration:Q", title="Vibration (g)", scale=alt.Scale(nice=True))
            )
            
            # Ligne de seuil (Altair) - FIX 4: size=2
            thr  = alt.Chart(pd.DataFrame({"y":[seuil]})).mark_rule(
                strokeDash=[4,4], 
                color="#ff4b4b",
                size=2 
            ).encode(y="y:Q")
            
            col_status, col_chart = st.columns([1, 4])
            
            # Détermination de l'état global
            derniere_mesure = dfc.iloc[-1]['Vibration']
            is_critique = derniere_mesure >= seuil
            
            with col_status:
                if is_critique:
                    st.error(f"⚠️ **CRITIQUE**\nVibration: {derniere_mesure:.3f} g")
                else:
                    st.success(f"✅ **SAFE**\nVibration: {derniere_mesure:.3f} g")

            with col_chart:
                st.altair_chart(line + thr, use_container_width=True)
            
    else:
        st.info("Aucune donnée simulée pour l'instant. L'auto-démo se lancera à l'ouverture de l'onglet." if lang=="FR" else "No simulated data yet. Auto-demo will start upon opening the tab.")

    st.markdown("---")
    
    st.markdown("### 📋 Dernières mesures" if lang=="FR" else "### 📋 Latest measurements")
    st.dataframe(
        st.session_state.sim_df.sort_index(ascending=False).reset_index(drop=True).head(10), 
        height=220, 
        use_container_width=True
    )

    # ----------------- Download CSV -----------------
    def to_csv_bytes(df: pd.DataFrame):
        # FIX 3: Ajout du BOM (Byte Order Mark) pour compatibilité Excel
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        return ("\ufeff" + buffer.getvalue()).encode("utf-8-sig")

    if not st.session_state.sim_df.empty:
        csv_bytes = to_csv_bytes(st.session_state.sim_df)
        st.download_button(
            "⬇️ Télécharger les données (CSV)" if lang=="FR" else "⬇️ Download data (CSV)", 
            data=csv_bytes, file_name="rekarbon_simulation.csv", mime="text/csv", 
            key="capteurs_download_csv"
        )
    else:
        st.caption("Les données seront téléchargeables après génération." if lang=="FR" else "Data will be downloadable after generation.")

    # ----------------- Logs & Status -----------------
    st.markdown("### 📝 Journal d'activité (logs)" if lang=="FR" else "### 📝 Activity Log (logs)")
    # FIX 2: Rendu monospaced (text) au lieu de markdown (write)
    log_col = st.empty()
    log_col.text("\n".join(list(st.session_state.log_history)[-30:]))

    st.caption("Mode démo sécurisé : aucune donnée n'est envoyée à des services externes." if lang=="FR" else "Secure demo mode: no data is sent to external services.")

    # ----------------- Petite explication (texte pour jurys) -----------------
    st.markdown("---")
    st.markdown(
        "**Note pour les examinateurs / investisseurs :**\n\n"
        "- Ce simulateur est en **mode démonstration**. Aucune requête réseau n'est effectuée.\n"
        "- Pour la preuve technique complète, le module Edge (Raspberry Pi) fonctionne en local et peut être montré lors d'une session privée.\n"
        "- Ici, vous pouvez cliquer, manipuler et télécharger des données simulées pour tester l'interface."
    )
    
    # Bouton de retour rapide via helper
    back_to_synthesis_button(lang, key="back_capteurs")


# ===================================================================
# FONCTION DE VALORISATION DES SARGASSES - CONSERVÉE DE VOTRE ZONE B
# ===================================================================
def simuler_valorisation_sargasses(lang):
    """
    Fonction maîtresse pour simuler la valorisation des sargasses
    en Biochar, Syngaz ou Bio-huile. (B)
    """
    st.subheader(T(lang, "sargasses_title"))
    info_msg = "Sélectionnez un scénario d'optimisation (Biochar, Syngaz ou Bio-huile) basé sur les paramètres ajustables ci-dessous." if lang == "FR" else "Select an optimization scenario (Biochar, Syngas, or Bio-oil) based on the adjustable parameters below."
    st.info(info_msg)

    # 1) Panneau paramètres communs (à mettre dans simuler_valorisation_sargasses)
    with st.sidebar.expander(T(lang, "sarg_settings")):
        base_tonnage = st.number_input(T(lang, "sarg_tonnage_wet"), 1.0, 1000.0, 10.0, 1.0, key="sarg_t_wet")
        humidite_pct = st.slider(T(lang, "sarg_moisture"), 50, 95, 85, 1, key="sarg_moist")
        # rendements sur matière sèche
        y_biochar = st.number_input(T(lang, "sarg_yield_bch"), 0.05, 0.60, 0.30, 0.01, key="y_bch")
        y_syngaz  = st.number_input(T(lang, "sarg_yield_syg"), 0.05, 0.90, 0.40, 0.01, key="y_syg")
        y_biooil  = st.number_input(T(lang, "sarg_yield_bho"), 0.05, 0.60, 0.30, 0.01, key="y_bho")
        # économie / valorisation
        prix_biochar_t = st.number_input(T(lang, "sarg_price_bch"), 0, 5000, 450, 10, key="p_bch")
        prix_biooil_t  = st.number_input(T(lang, "sarg_price_bho"), 0, 5000, 350, 10, key="p_bho")
        prix_kwh       = st.number_input(T(lang, "sarg_price_kwh"), 0.00, 5.00, 0.15, 0.01, key="p_kwh")
        kwh_per_t_syg  = st.number_input(T(lang, "sarg_kwh_per_t"), 0, 20000, 4000, 100, key="kwh_syg")

    # Calcul de matière sèche (MS)
    MS = base_tonnage * (1 - humidite_pct/100)
    
    st.markdown(f"**Matière brute traitée (humide):** {base_tonnage:.1f} t &nbsp;|&nbsp; **Matière Sèche (MS):** {MS:.2f} t")
    st.markdown("---")

    scenario_options_fr = {
        T("FR", "biochar_scenario"): "biochar",
        T("FR", "syngas_scenario"): "syngaz",
        T("FR", "biohuile_scenario"): "biohuile",
    }
    
    scenario_options_en = {
        T("EN", "biochar_scenario"): "biochar",
        T("EN", "syngas_scenario"): "syngaz",
        T("EN", "biohuile_scenario"): "biohuile",
    }

    # Utilisation des clés FR ou EN dans le selectbox
    scenario_labels = list(scenario_options_fr.keys()) if lang == "FR" else list(scenario_options_en.keys())
    
    selected_label = st.selectbox(
        "Choisissez l'optimisation à simuler :" if lang=="FR" else "Choose optimization to simulate:",
        scenario_labels,
        key="sargasses_scenario_choice"
    )

    # Détermination de la route interne
    route_key = scenario_options_fr[selected_label] if lang == "FR" else scenario_options_en[selected_label]

    results = []
    
    # 2) Appel des fonctions avec les paramètres calculés
    if route_key == "biochar":
        results.append(simuler_sargasses_biochar(lang, MS, y_biochar, prix_biochar_t))
    elif route_key == "syngaz":
        results.append(simuler_sargasses_syngaz(lang, MS, y_syngaz, prix_kwh, kwh_per_t_syg))
    elif route_key == "biohuile":
        results.append(simuler_sargasses_biohuile(lang, MS, y_biooil, prix_biooil_t))

    st.markdown("---")

    # 3) Export CSV du résultat affiché
    df_res = pd.DataFrame(results)
    csv = df_res.to_csv(index=False).encode("utf-8")
    st.download_button(T(lang, "sarg_export"),
                        data=csv, file_name="sargasses_result.csv", mime="text/csv",
                        key="sargasses_csv")

    back_to_synthesis_button(lang, key="back_sargasses_main")

def simuler_sargasses_biochar(lang, MS, y_biochar, prix_biochar_t, co2_seq_tonne_biochar=2.5):
    """Calcule la valorisation Biochar avec les paramètres du sidebar."""
    biochar_produit = MS * y_biochar
    co2_sequestre = biochar_produit * co2_seq_tonne_biochar
    valeur = biochar_produit * prix_biochar_t
    tokens_generes = int(co2_sequestre * 100)

    st.markdown("#### 1/3 " + (T(lang, "biochar_scenario")))
    # FIX: Correction du libellé "tonnage humide" -> "MS (t)"
    st.markdown(f"**MS (t)**: {MS:.2f} &nbsp;|&nbsp; **{T(lang,'sarg_yield_bch')}**: {y_biochar:.2f}")

    c1,c2,c3 = st.columns(3)
    c1.metric("Biochar (t)", f"{biochar_produit:.2f}")
    c2.metric("CO₂ séquestré (t)", f"{co2_sequestre:.2f}")
    c3.metric("Valeur (€)", eur(valeur)) # Utilisation de eur(x)
    
    st.success(f"Tokens REKAR ~ {tokens_generes:,}".replace(',', ' '))
    
    report_content = {
        "MS (t)": f"{MS:.2f}",
        T(lang, 'sarg_yield_bch'): f"{y_biochar:.2f} t/t MS",
        "Biochar Produit (t)": f"{biochar_produit:.2f}",
        "CO2 séquestré (t)": f"{co2_sequestre:.2f}",
        "Tokens REKAR générés": f"{tokens_generes:,}".replace(',', ' '),
        "Valorisation (€)": eur(valeur),
    }
    
    if st.button(f"📄 {T(lang,'report')} Biochar", key="pdf_sargasses_biochar"):
        pdf_file = generate_pdf("Sargasses – Biochar", report_content)
        st.download_button(f"📥 {T(lang,'download')}", data=pdf_file, file_name="sargasses_biochar.pdf", mime="application/pdf", key="dl_sarg_bch")
    
    return {"Voie": T(lang, "biochar_scenario"), "MS (t)": f"{MS:.2f}", "Biochar (t)": f"{biochar_produit:.2f}", "CO2 (t)": f"{co2_sequestre:.2f}", "Valeur (€)": eur(valeur)}

def simuler_sargasses_syngaz(lang, MS, y_syngaz, prix_kwh, kwh_per_t_syg):
    """Calcule la valorisation Syngaz avec les paramètres du sidebar."""
    syngaz_produit = MS * y_syngaz
    energie_produite_kwh = syngaz_produit * kwh_per_t_syg
    valeur = energie_produite_kwh * prix_kwh
    
    st.markdown("#### 2/3 " + (T(lang, "syngas_scenario")))
    # FIX 5: Uniformité unités / labels (MS (t) au lieu de Matière sèche (MS)
    st.markdown(f"**MS (t)**: {MS:.2f} &nbsp;|&nbsp; **Rendement Syngaz**: {y_syngaz:.2f} t/t MS")

    c1,c2,c3 = st.columns(3)
    c1.metric("Syngaz (t)", f"{syngaz_produit:.2f}")
    c2.metric("Énergie (kWh)", f"{energie_produite_kwh:,.0f}".replace(',', ' '))
    c3.metric("Valeur (€)", eur(valeur))
    
    st.success("✅ BILAN : Production d'énergie locale maximisée." if lang=="FR" else "✅ SUMMARY: Local energy production maximized.")

    report_content = {
        "MS (t)": f"{MS:.2f}", # FIX 2: Cohérence unités
        "Rdt Syngaz (t/t MS)": f"{y_syngaz:.2f}",
        "Syngaz Produit (t)": f"{syngaz_produit:.2f}",
        "Énergie Générée (kWh)": f"{energie_produite_kwh:,.0f}".replace(',', ' '),
        "Valeur Énergétique (€)": eur(valeur),
    }
    
    if st.button(f"📄 {T(lang,'report')} Syngaz", key="pdf_sargasses_syngaz"):
        pdf_file = generate_pdf("Sargasses – Syngaz", report_content)
        st.download_button(f"📥 {T(lang,'download')}", data=pdf_file, file_name="rapport_sargasses_syngaz.pdf", mime="application/pdf", key="dl_sarg_syg")
        
    return {"Voie": T(lang, "syngas_scenario"), "MS (t)": f"{MS:.2f}", "Syngaz (t)": f"{syngaz_produit:.2f}", "Énergie (kWh)": f"{energie_produite_kwh:,.0f}".replace(',', ' '), "Valeur (€)": eur(valeur)}

def simuler_sargasses_biohuile(lang, MS, y_biooil, prix_biooil_t):
    """Calcule la valorisation Bio-huile avec les paramètres du sidebar."""
    biohuile_produite = MS * y_biooil
    valeur = biohuile_produite * prix_biooil_t
    
    st.markdown("#### 3/3 " + (T(lang, "biohuile_scenario")))
    st.markdown(f"**Matière sèche (MS)**: {MS:.2f} t &nbsp;|&nbsp; **Rendement Bio-huile**: {y_biooil:.2f} t/t MS")

    c1,c2,c3 = st.columns(3)
    c1.metric("Bio-huile (t)", f"{biohuile_produite:.2f}")
    c2.metric("Substitut Pétrolier", "Élevé" if lang=="FR" else "High")
    c3.metric("Valeur (€)", eur(valeur))
    
    st.success("✅ BILAN : Production de base chimique/carburant maximisée." if lang=="FR" else "✅ SUMMARY: Chemical/fuel base production maximized.")

    report_content = {
        "MS (t)": f"{MS:.2f}", # FIX 2: Cohérence unités
        "Rdt Bio-huile (t/t MS)": f"{y_biooil:.2f}",
        "Bio-huile Produite (t)": f"{biohuile_produite:.2f}",
        "Valeur Commerciale (€)": eur(valeur),
    }
    
    if st.button(f"📄 {T(lang,'report')} Bio-huile", key="pdf_sargasses_biohuile"):
        pdf_file = generate_pdf("Sargasses – Bio-huile", report_content)
        st.download_button(f"📥 {T(lang,'download')}", data=pdf_file, file_name="rapport_sargasses_biohuile.pdf", mime="application/pdf", key="dl_sarg_bho")
        
    return {"Voie": T(lang, "biohuile_scenario"), "MS (t)": f"{MS:.2f}", "Bio-huile (t)": f"{biohuile_produite:.2f}", "Valeur (€)": eur(valeur)}


# ===================================================================
# VOS 10 FONCTIONS DE SIMULATION EXISTANTES (MISE À JOUR) - CONSERVÉES DE VOTRE ZONE B
# ===================================================================
def simuler_maintenance_predictive_v2(scenario='Normal', lang="FR"):
    st.subheader(T(lang, "maint_sim_title"))
    report_content = {}
    
    # Logique inchangée pour les données et l'analyse
    if scenario == 'Alerte':
        data = {'timestamp': pd.to_datetime(['18:20:01', '18:20:02', '18:20:03', '18:20:04', '18:20:05'], format='%H:%M:%S').time, 'vibration_level': [0.21, 0.23, 0.22, 0.85, 0.87], 'temperature_celsius': [45, 46, 45, 68, 70], 'power_consumption_kw': [150.5, 151.0, 150.2, 185.7, 188.1]}
        df = pd.DataFrame(data).set_index('timestamp')
        st.subheader("📈 Données des Capteurs en Temps Réel" if lang=="FR" else "📈 Real-time Sensor Data")
        st.line_chart(df, use_container_width=True) 
        with st.spinner("ANALYSE (IA Rekarbon)..."): time.sleep(1.5)
        latest_data = df.iloc[-1]
        st.error("⚠️ ALERTE SYSTÈME : Risque de défaillance critique détecté !" if lang=="FR" else "⚠️ SYSTEM ALERT: Critical failure risk detected!", icon="🚨")
        col1, col2, col3 = st.columns(3)
        col1.metric("Vibration" if lang=="FR" else "Vibration", f"{latest_data['vibration_level']} g", "Élevé" if lang=="FR" else "High")
        col2.metric("Température" if lang=="FR" else "Temperature", f"{latest_data['temperature_celsius']} °C", "Critique" if lang=="FR" else "Critical")
        col3.metric("Consommation" if lang=="FR" else "Consumption", f"{latest_data['power_consumption_kw']} kW", "+25%")
        st.warning("**Synthèse IA :** Corrélation anormale détectée, probabilité de défaillance imminente de 98%." if lang=="FR" else "**AI Synthesis:** Abnormal correlation detected, 98% probability of imminent failure.")
        st.success("✅ ACTIONS INITIÉES : Ticket créé, pièce commandée, ligne de production mise en sécurité." if lang=="FR" else "✅ ACTIONS INITIATED: Ticket created, part ordered, production line secured.")
        report_content = {"Statut": "ALERTE" if lang=="FR" else "ALERT", "Diagnostic": "Probabilité de défaillance de 98% (roulement SKF-6203)", "Actions": ["Arrêt de la ligne 'Broyage'" if lang=="FR" else "Stopping 'Grinding' line", "Commande automatique de la pièce" if lang=="FR" else "Automatic part order", "Assignation d'un ticket de maintenance prioritaire" if lang=="FR" else "Assigning priority maintenance ticket"]}
    else: 
        data = {'timestamp': pd.to_datetime(['18:20:01', '18:20:02', '18:20:03', '18:20:04', '18:20:05'], format='%H:%M:%S').time, 'vibration_level': [0.21, 0.23, 0.22, 0.24, 0.21], 'temperature_celsius': [45, 46, 45, 47, 46], 'power_consumption_kw': [150.5, 151.0, 150.2, 152.0, 151.5]}
        df = pd.DataFrame(data).set_index('timestamp')
        st.subheader("📈 Données des Capteurs en Temps Réel" if lang=="FR" else "📈 Real-time Sensor Data")
        st.line_chart(df, use_container_width=True) 
        with st.spinner("ANALYSE (IA Rekarbon)..."): time.sleep(1.5)
        st.success("✅ STATUT : Tous les systèmes du broyeur sont opérationnels." if lang=="FR" else "✅ STATUS: All grinder systems are operational.", icon="👍")
        report_content = {"Statut": "NORMAL", "Diagnostic": "Aucune anomalie détectée" if lang=="FR" else "No anomaly detected", "Actions": "Aucune action requise" if lang=="FR" else "No action required"}
    
    if st.button(f"📄 Générer le {T(lang, 'report')} d'Intervention", key="pdf_maintenance"):
        pdf_file = generate_pdf("Rapport de Maintenance Prédictive" if lang=="FR" else "Predictive Maintenance Report", report_content)
        st.download_button(f"📥 {T(lang, 'download')}", data=pdf_file, file_name="rapport_maintenance.pdf", mime="application/pdf", key="download_maintenance")
    
    back_to_synthesis_button(lang, key="back_maintenance")


def simuler_optimisation_logistique_v2(lang="FR"):
    st.subheader(T(lang, "log_sim_title"))
    with st.spinner(f"{T(lang, 'analyze')} (IA Rekarbon): Analyse des inventaires, commandes et capacité de production..."):
        time.sleep(2.5)
    data_inventaire = {'Produit': ['Bio-huile', 'Biochar Granulé', 'Engrais Liquide'], 'Stock Actuel (tonnes)': [15, 80, 45], 'Commandes à Honorer (tonnes)': [40, 65, 20]}
    df_inventaire = pd.DataFrame(data_inventaire)
    produit_critique = df_inventaire.loc[0]
    deficit = produit_critique['Commandes à Honorer (tonnes)'] - produit_critique['Stock Actuel (tonnes)']
    st.subheader("📦 État des Stocks Actuels" if lang=="FR" else "📦 Current Stock Status")
    st.dataframe(df_inventaire, use_container_width=True) 
    st.subheader(f"📊 Analyse du Produit Critique : {produit_critique['Produit']}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Stock Actuel" if lang=="FR" else "Current Stock", f"{produit_critique['Stock Actuel (tonnes)']} t")
    col2.metric("Commandes à Honorer" if lang=="FR" else "Orders to fulfill", f"{produit_critique['Commandes à Honorer (tonnes)']} t")
    col3.metric("Déficit" if lang=="FR" else "Deficit", f"{deficit} t", delta_color="inverse")
    st.error("⚠️ ALERTE LOGISTIQUE : Rupture de stock imminente sur la ligne 'Bio-huile'." if lang=="FR" else "⚠️ LOGISTICS ALERT: Imminent stock shortage for 'Bio-oil'.", icon="📦")
    with st.spinner("DÉCISION (IA Rekarbon): Formulation d'un plan d'action correctif..." if lang=="FR" else "DECISION (Rekarbon AI): Formulating corrective action plan..."):
        time.sleep(2)
    st.success("✅ PLAN D'ACTION PROPOSÉ:" if lang=="FR" else "✅ PROPOSED ACTION PLAN:")
    action_plan = ["**Production :** Augmenter la cadence de 15%." if lang=="FR" else "**Production:** Increase throughput by 15%.", "**Commercial :** Contacter 'Client-ABC' pour livraison partielle." if lang=="FR" else "**Sales:** Contact 'Client-ABC' for partial delivery.", "**Achats :** Commande d'urgence de matière première." if lang=="FR" else "**Procurement:** Emergency order of raw material."]
    st.info("\n".join(f"{i+1}. {item}" for i, item in enumerate(action_plan)))
    report_content = {"Statut": "ALERTE STOCK" if lang=="FR" else "STOCK ALERT", "Produit Critique": "Bio-huile", "Déficit": f"{deficit} tonnes", "Plan d'action": action_plan}
    
    if st.button(f"📄 Générer le {T(lang, 'report')} Logistique", key="pdf_logistique"):
        pdf_file = generate_pdf("Rapport d'Optimisation Logistique" if lang=="FR" else "Logistics Optimization Report", report_content)
        st.download_button(f"📥 {T(lang, 'download')}", data=pdf_file, file_name="rapport_logistique.pdf", mime="application/pdf", key="download_logistique")
        
    back_to_synthesis_button(lang, key="back_logistique")
        
def simuler_livraison_temps_pluie_v2(lang="FR"):
    st.subheader("⛈️ Simulation : Itinéraire de Livraison Météo-dépendant" if lang=="FR" else "⛈️ Simulation: Weather-Dependent Delivery Route")
    # ... (code de simulation inchangé)
    if st.button(f"📄 Générer le {T(lang, 'report')} de Trajet", key="pdf_livraison"):
        pdf_file = generate_pdf("Rapport de Livraison" if lang=="FR" else "Delivery Report", {"Alerte": "Pluies fortes"})
        st.download_button(f"📥 {T(lang, 'download')}", data=pdf_file, file_name="rapport_livraison.pdf", mime="application/pdf", key="download_livraison")
    back_to_synthesis_button(lang, key="back_livraison")

def simuler_vente_et_tokenisation_v2(lang="FR"):
    st.subheader("🔥 Simulation : Vente de Biochar & Tokenisation" if lang=="FR" else "🔥 Simulation: Biochar Sales & Tokenization")
    # ... (code de simulation inchangé)
    if st.button(f"📄 Générer la Facture", key="pdf_vente"):
        pdf_file = generate_pdf("Facture de Vente Biochar" if lang=="FR" else "Biochar Sales Invoice", {"Client": "Client Industriel SAS"})
        st.download_button(f"📥 {T(lang, 'download')}", data=pdf_file, file_name="facture_biochar.pdf", mime="application/pdf", key="download_vente")
    back_to_synthesis_button(lang, key="back_vente")

def simuler_reforestation_et_carbone_v2(lang="FR"):
    st.subheader("🌳 Simulation : Reforestation & Crédits Carbone" if lang=="FR" else "🌳 Simulation: Reforestation & Carbon Credits")
    # ... (code de simulation inchangé)
    if st.button(f"📄 Générer le Certificat", key="pdf_reforestation"):
        pdf_file = generate_pdf("Certificat de Crédits Carbone" if lang=="FR" else "Carbon Credits Certificate", {"Parcelle": "REK-AF-01"})
        st.download_button(f"📥 {T(lang, 'download')}", data=pdf_file, file_name="certificat_carbone.pdf", mime="application/pdf", key="download_reforestation")
    back_to_synthesis_button(lang, key="back_reforestation")

def simuler_cession_token(lang="FR"):
    st.subheader("🔁 Simulation : Cession de Tokens B2B" if lang=="FR" else "🔁 Simulation: B2B Token Transfer")
    # ... (code de simulation inchangé)
    if st.button(f"📄 Générer l'Ordre de Transfert", key="pdf_cession"):
        pdf_file = generate_pdf("Ordre de Transfert de Tokens" if lang=="FR" else "Token Transfer Order", {"Cédant": "Client A"})
        st.download_button(f"📥 {T(lang, 'download')}", data=pdf_file, file_name="ordre_transfert_rekar.pdf", mime="application/pdf", key="download_cession")
    back_to_synthesis_button(lang, key="back_cession")

def simuler_rapport_fmi(lang="FR"):
    st.subheader("🌍 Rapport : Demande de Financement FMI (Maurice)" if lang=="FR" else "🌍 Report: IMF Financing Request (Mauritius)")
    # ... (code de simulation inchangé)
    if st.button(f"📄 Générer la Synthèse pour le FMI", key="pdf_fmi"):
        pdf_file = generate_pdf("Synthèse Exécutive - Projet Rekarbon Maurice" if lang=="FR" else "Executive Summary - Rekarbon Mauritius Project", {"Porteur de projet": "Rekarbon (Maurice)"})
        st.download_button(f"📥 {T(lang, 'download')}", data=pdf_file, file_name="synthese_fmi_rekarbon.pdf", mime="application/pdf", key="download_fmi")
    back_to_synthesis_button(lang, key="back_fmi")
        
def simuler_rapport_commune(lang="FR"):
    st.subheader("🇷🇪 Rapport : Financement Européen (Saint-Paul)" if lang=="FR" else "🇷🇪 Report: European Financing (Saint-Paul)")
    # ... (code de simulation inchangé)
    if st.button(f"📄 Générer la Fiche Projet", key="pdf_commune"):
        pdf_file = generate_pdf("Fiche Projet FEDER - Rekarbon Saint-Paul" if lang=="FR" else "FEDER Project Sheet - Rekarbon Saint-Paul", {"Commune": "Saint-Paul, La Réunion"})
        st.download_button(f"📥 {T(lang, 'download')}", data=pdf_file, file_name="fiche_projet_stpaul.pdf", mime="application/pdf", key="download_commune")
    back_to_synthesis_button(lang, key="back_commune")

def simuler_vente_bio_huile(lang="FR"):
    st.subheader("🧴 Simulation : Vente Produit Fini (Bio-Huile)" if lang=="FR" else "🧴 Simulation: Finished Product Sale (Bio-Oil)")
    # ... (code de simulation inchangé)
    if st.button(f"📄 Générer le Bon de Livraison", key="pdf_biohuile"):
        pdf_file = generate_pdf("Bon de Livraison - Bio-huile" if lang=="FR" else "Delivery Note - Bio-oil", {"Produit": "Bio-huile 'Source des Hauts' 5L"})
        st.download_button(f"📥 {T(lang, 'download')}", data=pdf_file, file_name="bl_biohuile.pdf", mime="application/pdf", key="download_biohuile")
    back_to_synthesis_button(lang, key="back_biohuile")

def simuler_reforestation_ciblee(lang="FR"):
    st.subheader("🌲 Simulation : Reforestation Ciblée (Grand-Coude)" if lang=="FR" else "🌲 Simulation: Targeted Reforestation (Grand-Coude)")
    # ... (code de simulation inchangé)
    if st.button(f"📄 Générer le Certificat de Plantation", key="pdf_reforestation_ciblee"):
        pdf_file = generate_pdf("Certificat de Plantation" if lang=="FR" else "Planting Certificate", {"Localisation": "Grand-Coude, La Réunion"})
        st.download_button(f"📥 {T(lang, 'download')}", data=pdf_file, file_name="certificat_plantation.pdf", mime="application/pdf", key="download_reforestation_ciblee")
    back_to_synthesis_button(lang, key="back_refo_ciblee")

# ===================================================================
# GESTION DU ROUTAGE STABLE (VOTRE ZONE B COMMENCE VRAIMENT ICI)
# ===================================================================
ROUTES = {
    "synth": simuler_tableau_de_bord_kpis,
    "sensor": simuler_capteurs_safe_interactive,
    "sargassum": simuler_valorisation_sargasses,
    "maint": simuler_maintenance_predictive_v2,
    "log": simuler_optimisation_logistique_v2,
    "rain": simuler_livraison_temps_pluie_v2,
    "sale": simuler_vente_et_tokenisation_v2,
    "forest": simuler_reforestation_et_carbone_v2,
    "transfer": simuler_cession_token,
    "imf": simuler_rapport_fmi,
    "city": simuler_rapport_commune,
    "biooil": simuler_vente_bio_huile,
    "targetforest": simuler_reforestation_ciblee,
    "energy_analysis": simuler_analyse_energetique, # AJOUT DE LA NOUVELLE ROUTE
    "revenue_calc": simuler_revenue_link, # NOUVELLE ROUTE
}

MENU_LABELS = {
    "FR": {
        "synth": T("FR","synth_title"),
        "sensor": T("FR","sensor_sim_title"),
        "sargassum": T("FR","sargasses_title"),
        "maint": T("FR","maint_sim_title"),
        "log": T("FR","log_sim_title"),
        "rain": "Livraison (Météo)",
        "sale": "Vente & Tokenisation",
        "forest": "Reforestation & Carbone",
        "transfer": "Cession de Tokens (B2B)",
        "imf": "Rapport FMI (Maurice)",
        "city": "Rapport Local (St-Paul)",
        "biooil": "Vente Produit (Bio-Huile)",
        "targetforest": "Reforestation (Grand-Coude)",
        "energy_analysis": "Analyse Edge (Énergie)", # NOUVEAU LABEL
        "revenue_calc": T("FR", "revenue_calc_title"), # NOUVEAU LABEL
    },
    "EN": {
        "synth": T("EN","synth_title"),
        "sensor": T("EN","sensor_sim_title"),
        "sargassum": T("EN","sargasses_title"),
        "maint": T("EN","maint_sim_title"),
        "log": T("EN","log_sim_title"),
        "rain": "Delivery (Weather)",
        "sale": "Sales & Tokenization",
        "forest": "Reforestation & Carbon",
        "transfer": "Token Transfer (B2B)",
        "imf": "IMF Report (Mauritius)",
        "city": "Local Report (St-Paul)",
        "biooil": "Finished Product (Bio-Oil)",
        "targetforest": "Targeted Reforestation",
        "energy_analysis": "Edge Analysis (Energy)", # NOUVEAU LABEL
        "revenue_calc": T("EN", "revenue_calc_title"), # NOUVEAU LABEL
    }
}

def get_label(lang, route): return MENU_LABELS[lang].get(route, route) # Utilisation de .get pour plus de robustesse

# ===================================================================
# INTERFACE UTILISATEUR ET LOGIQUE D'AUTO-DÉMARRAGE - CONSERVÉE DE VOTRE ZONE B
# ===================================================================
# ATTENTION: J'ai retiré le st.sidebar.radio("Language / Langue", ...) statique ici
# car nous l'avons déplacé en haut du script.

TITLE = T(lang, "title")
CAPTION = T(lang, "caption")
MENU_TITLE = T(lang, "menu_title")
SELECT_PROMPT = T(lang, "choose_sim") 
SCENARIO_PROMPT = T(lang, "choose_state")

st.title(TITLE)
st.caption(CAPTION)
st.sidebar.title(MENU_TITLE)

# Gestion du retour rapide à la Synthèse
if st.session_state.get("_return_to_synth"):
    st.session_state["_return_to_synth"] = False
    default_route = "synth"
else:
    default_route = "synth"

# --- FIX B: Fallback si st.query_params n'est pas dispo ---
try:
    qp_get = st.query_params.get
    qp_set = lambda k,v: st.query_params.__setitem__(k,v)
except Exception:
    # Si le contexte n'a pas st.query_params (ancien Streamlit ou environnement restreint)
    qp = st.experimental_get_query_params()
    qp_get = lambda k: qp.get(k, [None])[0]
    qp_set = lambda k,v: st.experimental_set_query_params(**{k:v})
# --- Fin FIX B ---

# --- Sidebar selectbox piloté par route-id ---
routes = list(ROUTES.keys())
labels = [get_label(lang, r) for r in routes]
page_qp = qp_get("page")

# Détermination de la route initiale (deep-link > retour rapide > défaut)
route = page_qp if page_qp in ROUTES else default_route
idx = routes.index(route)

selected_label = st.sidebar.selectbox(SELECT_PROMPT, labels, index=idx, key="menu_choice")
# Retrouver l'ID de route stable à partir du label sélectionné
route = routes[labels.index(selected_label)]

if page_qp != route:
    qp_set("page", route)
# --- Fin routage stable ---

# Point 1: Seuils contrôlables pour le Simulateur de Capteurs
if route == "sensor":
    # Le seuil n'est visible que si l'onglet Capteurs est sélectionné.
    with st.sidebar.expander(T(lang, "params")):
        st.session_state.setdefault("seuil_vib", VIBRATION_SEUIL_DEFAUT)
        st.session_state.seuil_vib = st.slider(
            T(lang, "vib_thr"), 
            0.9, 2.0, float(st.session_state.seuil_vib), 0.01, key="seuil_slider" 
        )
# Point 2: Les paramètres pour l'Analyse Énergie sont maintenant gérés dans la fonction simuler_analyse_energetique

else:
    # Initialisation / maintien de la valeur par défaut pour les autres onglets
    st.session_state.setdefault("seuil_vib", VIBRATION_SEUIL_DEFAUT)


fn = ROUTES[route]

# Logique de lancement
if route == "sensor":
    fn(auto_run=True, seuil_alerte_defaut=st.session_state.seuil_vib, lang=lang) 

elif route == "maint":
    # Utilisation de T() pour les options du radio
    scenario_choisi = st.sidebar.radio(SCENARIO_PROMPT, (T(lang, "run_state_normal"), T(lang, "run_state_alert")), key='maintenance_scenario')
    
    # Bouton de lancement
    BTN_RUN_MAINT = T(lang, "run_sim")
    if st.button(f"{BTN_RUN_MAINT} ({scenario_choisi})", key="run_maintenance"):
        # Traduction du scénario sélectionné pour le code métier (Normal/Alerte)
        scenario_key = 'Alerte' if scenario_choisi == T(lang, "run_state_alert") else 'Normal'
        fn(scenario=scenario_key, lang=lang)
    
elif route == "synth":
    fn(lang=lang)

elif route == "sargassum":
    # La fonction gère ses propres paramètres dans le sidebar.
    fn(lang=lang)

elif route == "energy_analysis":
    # La fonction gère tous ses éléments (sliders, affichage, etc.)
    fn(lang=lang)

elif route == "revenue_calc": # NOUVELLE ROUTE
    fn(lang=lang)
    
# Logique pour les autres simulations (bouton de lancement simple)
else:
    BTN_RUN_OTHER = T(lang, "run_sim")
    if st.button(BTN_RUN_OTHER, key=f"run_{route}"):
        fn(lang=lang)
        
# ==========================================================
# Bannière publique bilingue + boutons (avec effet hover pro)
# ==========================================================
st.markdown("---")

# Styles globaux (pour hover et animations)
st.markdown("""
<style>
.demo-banner {
    background: linear-gradient(90deg, #0f5132 0%, #198754 100%);
    color: white;
    padding: 18px;
    border-radius: 10px;
    margin-top: 25px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    font-family: 'Segoe UI', sans-serif;
}
.demo-buttons {
    text-align: center;
    margin-top: 15px;
    display: flex;
    justify-content: center;
    gap: 20px;
}
.demo-buttons a {
    background-color: #198754;
    color: white;
    padding: 10px 25px;
    border-radius: 8px;
    text-decoration: none;
    font-weight: bold;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
    transition: all 0.3s ease-in-out;
}
.demo-buttons a:hover {
    transform: scale(1.05);
    opacity: 0.9;
}
.demo-buttons a.site {
    background-color: #0f5132;
}
</style>
""", unsafe_allow_html=True)

if lang == "FR":
    st.markdown("""
    <div class="demo-banner">
        <h3>🔒 Rekarbon Edge Twin — Version Démo Sécurisée</h3>
        <p>Cette interface Streamlit présente une <b>démonstration publique partielle</b> 
        du système <b>Rekarbon Edge Twin</b>.<br>
        Les modules sensibles (connexion <b>Supabase</b>, <b>tokenisation blockchain</b>,
        <b>inférence IA</b>) ont été désactivés pour des raisons de sécurité.</p>
        <p>La version complète fonctionne en <b>local sur Raspberry Pi (Edge Native)</b> 
        et peut être présentée en <b>session privée technique</b> sur demande.</p>
    </div>

    <div class="demo-buttons">
        <a href="mailto:support@rekarbon.com?subject=Demande de démonstration privée — Rekarbon Edge Twin">📩 Demander une démonstration privée</a>
        <a href="https://www.rekarbon.com" target="_blank" rel="noopener" class="site">🌐 Visiter notre site rekarbon.com</a>
    </div>
    """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div class="demo-banner">
        <h3>🔒 Rekarbon Edge Twin — Secured Demo Version</h3>
        <p>This Streamlit interface shows a <b>partial public demo</b> 
        of the <b>Rekarbon Edge Twin</b> system.<br>
        Sensitive modules (<b>Supabase</b> authentication, <b>blockchain tokenization</b>,
        <b>AI inference pipelines</b>) have been disabled for security reasons.</p>
        <p>The full version runs locally on <b>Raspberry Pi (Edge Native)</b> 
        and can be shown in a <b>private technical session</b> upon request.</p>
    </div>

    <div class="demo-buttons">
        <a href="mailto:support@rekarbon.com?subject=Private demo request — Rekarbon Edge Twin">📩 Request a private demo</a>
        <a href="https://www.rekarbon.com" target="_blank" rel="noopener" class="site">🌐 Visit rekarbon.com</a>
    </div>
    """, unsafe_allow_html=True)
