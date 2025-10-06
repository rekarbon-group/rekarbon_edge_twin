import streamlit as st
import pandas as pd
import time
import numpy as np 
from datetime import datetime
from fpdf import FPDF
from io import BytesIO
import altair as alt # Import pour le graphique de seuil
import io # FIX 1: Ajout de l'import io
from collections import deque # FIX 5: Ajout de deque pour les logs
import locale # FIX C: Ajout de locale pour le format monétaire FR

# FIX C: Configuration locale pour le format monétaire FR
try:
    # Tente de configurer le format français
    locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
except locale.Error:
    try:
        # Fallback pour certains systèmes
        locale.setlocale(locale.LC_ALL, 'fra_FRA')
    except locale.Error:
        pass # Laisser le fallback de la fonction eur(x) gérer

def eur(x): 
    """Formate la valeur en devise française avec fallback manuel."""
    try: 
        return locale.currency(x, grouping=True, symbol=True)
    except Exception: 
        # Fallback manuel si locale.setlocale échoue sur le serveur
        return f"€ {x:,.0f}".replace(',', ' ')


# ===================================================================
# CONFIGURATION ET STYLE STREAMLIT
# ===================================================================
st.set_page_config(page_title="Rekarbon Edge Twin", page_icon="♻️", layout="wide")

# Masquer le menu, header et footer par défaut (style deeptech propre)
st.markdown("""
<style>
#MainMenu, header, footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ===================================================================
# CONFIGURATION GLOBALE ET SÉCURITÉ
# ===================================================================
SUPABASE_URL = None
SUPABASE_KEY = None

TEMP_NORMALE = 130.0
HUMIDITE_CIBLE = 12.0
VIBRATION_SEUIL_DEFAUT = 1.3 # Valeur par défaut avant l'initialisation du slider
SEED = 42 # Seed pour la reproductibilité de la démo

# ===================================================================
# I18N (INTERNATIONALISATION MINIMALE)
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
    },
}

def T(lang, key): 
    """Helper function for translation."""
    return I18N.get(lang, I18N["FR"]).get(key, key)


# ===================================================================
# FONCTIONS UTILITAIRES POUR PDF ET NAVIGATION
# ===================================================================
def back_to_synthesis_button(lang, key):
    """Génère le bouton de retour à la synthèse et déclenche un rerun."""
    st.markdown("---")
    if st.button(T(lang, "back"), key=key):
        st.session_state["_return_to_synth"] = True
        st.rerun()

def generate_pdf(simulation_title, report_data):
    pdf = FPDF()
    pdf.add_page()
    
    # Helper pour encoder de manière sûre en latin-1 pour le PDF
    def _safe_txt(x):
        s = str(x).replace("•", "-") # Remplacement de la puce pour la robustesse
        s = s.replace("€", "EUR ") # FIX 1: Remplacer € par EUR pour compatibilité FPDF Latin-1
        try:
            s.encode("latin-1")
            return s
        except UnicodeEncodeError:
            # Fallback en cas d'erreur d'encodage
            return s.encode("latin-1", "replace").decode("latin-1")

    # Robustesse PDF - Changement de police standard "Arial" à "Helvetica"
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, _safe_txt('Rekarbon - Rapport de Simulation Confidentiel'), 0, 1, 'C')
    pdf.set_font("Helvetica", '', 8)
    # Utilisation de f-string pour le formatage de la date (plus propre)
    pdf.cell(0, 10, _safe_txt(f"Généré le : {datetime.now():%d/%m/%Y %H:%M:%S}"), 0, 1, 'C')
    pdf.ln(10)
    
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, _safe_txt(simulation_title), 0, 1, 'L')
    pdf.set_font("Helvetica", '', 11)
    
    # C) Micro-nits rapides: utilisation de field au lieu de key pour éviter l'ombre
    for field, value in report_data.items():
        pdf.set_font("Helvetica", 'B', 10)
        pdf.multi_cell(0, 8, f"- {_safe_txt(field)}:")
        pdf.set_font("Helvetica", '', 10)
        if isinstance(value, list):
            for item in value:
                pdf.multi_cell(0, 6, f"  - {_safe_txt(item)}") 
        else:
            pdf.multi_cell(0, 8, f"  {_safe_txt(value)}")
            
    # Sécurisation de l'output final
    # Utilisation de 'replace' dans encode pour éviter les crashes sur les caractères exotiques non gérés
    pdf_output = pdf.output(dest='S').encode('latin-1', 'replace') 
    return BytesIO(pdf_output)

# ===================================================================
# FONCTION DE SYNTHÈSE (PAGE D'ACCUEIL)
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
# NOUVELLE FONCTION DE SIMULATION INTERACTIVE (DÉMO EDGE)
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
    log_col.text("\n".join(list(st.session_state.log_lines)[-30:]))

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
# FONCTION DE VALORISATION DES SARGASSES
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
# VOS 10 FONCTIONS DE SIMULATION EXISTANTES (MISE À JOUR)
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
# GESTION DU ROUTAGE STABLE (A)
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
    }
}

def get_label(lang, route): return MENU_LABELS[lang][route]

# ===================================================================
# INTERFACE UTILISATEUR ET LOGIQUE D'AUTO-DÉMARRAGE
# ===================================================================
lang = st.sidebar.radio("Language / Langue", ["FR", "EN"], horizontal=True)

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
    fn(lang=lang)
    
# Logique pour les autres simulations (bouton de lancement simple)
else:
    BTN_RUN_OTHER = T(lang, "run_sim")
    if st.button(BTN_RUN_OTHER, key=f"run_{route}"):
        fn(lang=lang)
