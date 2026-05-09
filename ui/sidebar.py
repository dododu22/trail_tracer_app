import streamlit as st
import os
import pickle
from datetime import datetime, date
import json

def render_project_selector():
    """Affiche le menu de chargement des projets existants"""
    st.subheader("📁 Mes Projets")
    
    saved_files = []
    if os.path.exists("data"):
        saved_files = [f for f in os.listdir("data") if f.endswith(".pkl")]
        
    choix_projet = st.selectbox(
        "Charger une course sauvegardée", 
        options=["-- Nouveau Projet (Upload GPX) --"] + saved_files
    )
    
    projet_charge = None
    if choix_projet != "-- Nouveau Projet (Upload GPX) --":
        with open(f"data/{choix_projet}", "rb") as f:
            projet_charge = pickle.load(f)
            st.success("Projet chargé avec succès ! ⚡")
            
    return projet_charge


def render_strategy_settings(projet_charge):
    """Affiche les formulaires de stratégie et retourne les paramètres saisis"""
    st.markdown("---")
    st.subheader("⚙️ Stratégie")
    
    uploaded_file = None
    if projet_charge is None:
        uploaded_file = st.file_uploader("Trace GPX", type=["gpx"], label_visibility="collapsed")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        # Date par défaut = aujourd'hui ou la date sauvegardée
        def_date = projet_charge["race_date"] if projet_charge and "race_date" in projet_charge else date.today()
        race_date = st.date_input("Date", value=def_date)
    with col_t2:
        start_time = st.time_input("Départ", value=datetime.strptime("06:00", "%H:%M").time())

    
    st.subheader("2. Allure & Fatigue")

    # On cherche d'abord dans le projet chargé, SINON dans le profil coureur, SINON on met une valeur par défaut
    profil_coureur = {}
    if os.path.exists("data/runner_profile.json"):
        with open("data/runner_profile.json", "r") as f:
            profil_coureur = json.load(f)

    # Récupération des valeurs intelligentes
    def_bp = projet_charge["base_pace"] if projet_charge else profil_coureur.get("base_pace", 6.0)
    def_pdp = projet_charge["penalty_dplus"] if projet_charge else profil_coureur.get("penalty_dplus", 10.0)

    col1, col2 = st.columns(2)
    with col1:
        base_pace = st.number_input("Allure de base (min/km)", value=float(def_bp), step=0.5)
    with col2:
        penalty_dplus = st.number_input("Pénalité D+ (min/100m)", value=float(def_pdp), step=0.5)

    # --- LA CORRECTION EST ICI (On remet les curseurs de fatigue) ---
    st.markdown("**Dérive de fatigue**")
    col3, col4 = st.columns(2)
    with col3:
        def_fatigue_rate = projet_charge["fatigue_rate"] if projet_charge else 5.0
        fatigue_rate = st.number_input("Fatigue (%)", value=float(def_fatigue_rate), step=1.0, help="% de ralentissement")
    with col4:
        def_fatigue_int = projet_charge["fatigue_interval"] if projet_charge else 20
        fatigue_interval = st.number_input("Tous les (Km)", value=int(def_fatigue_int), step=5)

    st.markdown("---")
    st.markdown("**Points de passage**")
    interval_km = st.slider("Jalons auto (Km)", min_value=5, max_value=20, value=10, step=5)
    
    liste_ravitos_sauves = projet_charge.get("custom_ravitos", projet_charge.get("ravitos", [])) if projet_charge else []
    def_ravitos = ", ".join(map(str, liste_ravitos_sauves))
    
    ravitos_input = st.text_input("Km des ravitaillements (ex: 12.5, 27, 42)", value=def_ravitos)
    
    custom_ravitos = []
    if ravitos_input:
        try:
            custom_ravitos = [float(x.strip()) for x in ravitos_input.split(',')]
        except ValueError:
            st.error("Format invalide. Utilise des chiffres séparés par des virgules.")

    # On regroupe tous les réglages dans un dictionnaire propre
    settings = {
        "start_time": start_time,
        "base_pace": base_pace,
        "penalty_dplus": penalty_dplus,
        "fatigue_rate": fatigue_rate,
        "fatigue_interval": fatigue_interval,
        "interval_km": interval_km,
        "custom_ravitos": custom_ravitos,
        "race_date": race_date
    }
    
    return uploaded_file, settings