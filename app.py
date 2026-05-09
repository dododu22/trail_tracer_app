import streamlit as st

# --- IMPORTS BACKEND (Logique) ---
from utils.gpx_helper import process_gpx
from utils.pacer import generate_splits
from utils.weather import fetch_weather_for_splits
from utils.pacer import apply_nutrition_strategy

# --- IMPORTS FRONTEND (Composants UI) ---
from ui.navigation import render_navbar
from ui.sidebar import render_project_selector, render_strategy_settings
from ui.dashboard import render_map_section, render_table_section, render_export_and_save, render_elevation_profile
from ui.nutrition import render_nutrition_tab
from ui.settings import render_settings_tab

# --- CONFIGURATION ---
st.set_page_config(page_title="Ultra Pacer", page_icon="🏔️", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_and_process_gpx(gpx_string):
    return process_gpx(gpx_string)

# --- MAIN APP ---
def main():
    selected_tab = render_navbar()

    if selected_tab == "Course":
        col_param, col_map = st.columns([1, 2])
        
        # 1. UI : Récupération des entrées utilisateur (Sidebar)
        with col_param:
            projet_charge = render_project_selector()
            uploaded_file, settings = render_strategy_settings(projet_charge)

        # 2. LOGIQUE & RENDU (Main page)
        if uploaded_file is not None or projet_charge is not None:
            
            # Extraction des données
            if projet_charge:
                df_gpx = projet_charge["df_gpx"]
            else:
                gpx_string = uploaded_file.getvalue().decode("utf-8")
                df_gpx = load_and_process_gpx(gpx_string)
            
            df_splits = generate_splits(
                df_gpx, 
                settings["base_pace"], settings["penalty_dplus"], 
                settings["start_time"], settings["race_date"], 
                settings["interval_km"], settings["fatigue_rate"], 
                settings["fatigue_interval"], settings["custom_ravitos"]
            )
            
            # NOUVEAU : Appel Météo
            with st.spinner("Récupération de la météo hyper-locale..."):
                # On convertit en JSON pour que le cache Streamlit fonctionne bien
                df_splits = fetch_weather_for_splits(df_splits.to_json())
                
            df_splits = apply_nutrition_strategy(df_splits)
            # UI : Affichage des résultats
            with col_map:
                render_map_section(df_gpx, df_splits)
                render_elevation_profile(df_gpx, df_splits)
                
            df_display = render_table_section(df_gpx, df_splits)
            render_export_and_save(df_gpx, df_display, settings, uploaded_file, projet_charge)

        else:
            with col_map:
                st.info("👈 Charge ton fichier GPX pour générer le plan et la carte.")

    elif selected_tab == "Nutrition":
            render_nutrition_tab()

    elif selected_tab == "Réglages":
        render_settings_tab()

if __name__ == "__main__":
    main()