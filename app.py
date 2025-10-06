import streamlit as st
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Rekarbon Edge Twin", page_icon="♻️", layout="wide")

st.title("♻️ Rekarbon Edge Twin – Démo Streamlit")
st.caption("Données simulées en local — aucun envoi réseau.")

# Créer un DataFrame vide au démarrage
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Temps", "Température (°C)", "Vibration (g)", "Courant (A)"])

col1, col2 = st.columns(2)

with col1:
    if st.button("🔹 Lancer une mesure"):
        new_row = {
            "Temps": time.strftime("%H:%M:%S"),
            "Température (°C)": round(60 + np.random.randn(), 2),
            "Vibration (g)": round(0.9 + abs(np.random.randn() * 0.05), 3),
            "Courant (A)": round(2.0 + np.random.randn() * 0.05, 3)
        }
        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
        st.success("Mesure ajoutée !")

with col2:
    if st.button("🔄 Réinitialiser"):
        st.session_state.data = pd.DataFrame(columns=["Temps", "Température (°C)", "Vibration (g)", "Courant (A)"])
        st.info("Simulation réinitialisée.")

# Affichage du graphique et du tableau
if not st.session_state.data.empty:
    st.line_chart(st.session_state.data.set_index("Temps"))
    st.dataframe(st.session_state.data.tail(10))
else:
    st.info("Aucune donnée disponible. Cliquez sur 'Lancer une mesure' pour démarrer la démo.")
