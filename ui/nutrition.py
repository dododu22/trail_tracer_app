import streamlit as st
import json
import os

def render_nutrition_tab():
    st.title("🍎 Profil Nutritionnel")
    st.write("Définis tes cibles et tes portions. Ces paramètres seront utilisés pour calculer automatiquement tes besoins sur la carte de ta course.")

    # Chargement du profil existant si présent
    profile = {}
    if os.path.exists("data/nutrition_profile.json"):
        with open("data/nutrition_profile.json", "r") as f:
            profile = json.load(f)

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Tes cibles (par heure)")
        carbs_h = st.number_input("Glucides ciblés (g/h)", min_value=10, max_value=120, value=profile.get("carbs_h", 60), step=5)
        water_h = st.number_input("Hydratation ciblée (ml/h)", min_value=250, max_value=1200, value=profile.get("water_h", 500), step=50)

    with col2:
        st.subheader("📦 Tes portions physiques")
        gel_carbs = st.number_input("Apport d'un gel/barre (g de glucides)", min_value=5, max_value=50, value=profile.get("gel_carbs", 25), step=1)
        flask_vol = st.number_input("Volume d'une flasque (ml)", min_value=100, max_value=1000, value=profile.get("flask_vol", 500), step=50)

    st.info("💡 **Magie Météo :** L'algorithme majorera automatiquement tes besoins en eau de 25% sur les tronçons où la température prévue dépasse 22°C !")

    if st.button("💾 Enregistrer comme profil par défaut", use_container_width=True):
        os.makedirs("data", exist_ok=True)
        save_data = {
            "carbs_h": carbs_h,
            "water_h": water_h,
            "gel_carbs": gel_carbs,
            "flask_vol": flask_vol
        }
        with open("data/nutrition_profile.json", "w") as f:
            json.dump(save_data, f)
        st.success("Profil enregistré ! Retourne sur l'onglet 'Course' pour voir tes besoins s'afficher.")