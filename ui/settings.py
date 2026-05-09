import streamlit as st
import json
import os
from utils.biometrics import get_coeffs_from_score
from utils.strava_api import get_strava_auth_url, exchange_code_for_token, get_last_long_runs, analyze_fatigue_rate
import plotly.graph_objects as go


def render_settings_tab():
    st.title("⚙️ Réglages & Jumeau Numérique")
    st.write("Calibre ton jumeau numérique pour des prédictions d'allure sur-mesure.")
    
    # Chargement du profil existant
    profile = {}
    if os.path.exists("data/runner_profile.json"):
        with open("data/runner_profile.json", "r") as f:
            profile = json.load(f)

    # ==========================================
    # SECTION A : CALIBRATION ITRA / UTMB
    # ==========================================
    st.subheader("🏆 Calibration par Index de Performance (ITRA / UTMB)")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        itra_score = st.slider(
            "Ton score ou niveau estimé :", 
            min_value=200, max_value=900, 
            value=profile.get("itra_score", 450), 
            step=10
        )
    
    with col2:
        # On calcule en direct pour afficher le résultat avant de sauvegarder
        bp, pdp = get_coeffs_from_score(itra_score)
        st.info(f"🏃 Allure plat : **{bp} min/km**\n\n⛰️ Dénivelé : **+{pdp} min/100m**")

    if st.button("💾 Enregistrer comme mon profil coureur", use_container_width=True):
        os.makedirs("data", exist_ok=True)
        # On garde les anciennes données (comme la fatigue Strava) si elles existent
        profile["itra_score"] = itra_score
        profile["base_pace"] = bp
        profile["penalty_dplus"] = pdp
        
        with open("data/runner_profile.json", "w") as f:
            json.dump(profile, f)
        st.success("Profil enregistré ! Ces valeurs seront utilisées par défaut dans l'onglet Course.")

    st.markdown("---")

    # ==========================================
    # SECTION B : CONNEXION STRAVA
    # ==========================================
    st.subheader("🧡 Connexion Strava (Jumeau Numérique Réel)")
    st.write("Connecte ton compte pour analyser ta dérive de fatigue sur tes dernières sorties longues (>20km).")

    # 1. Vérification du retour de l'API Strava (quand l'utilisateur a cliqué sur "Autoriser")
    query_params = st.query_params
    if "code" in query_params and "strava_token" not in st.session_state:
        code = query_params["code"]
        with st.spinner("Authentification Strava en cours..."):
            try:
                token_response = exchange_code_for_token(code)
                if "access_token" in token_response:
                    st.session_state["strava_token"] = token_response["access_token"]
                    st.success("Connexion réussie !")
                    # On nettoie l'URL pour faire disparaître le "?code=..."
                    st.query_params.clear()
                else:
                    st.error("Erreur : Strava n'a pas renvoyé de jeton valide.")
            except Exception as e:
                st.error(f"Erreur de communication avec Strava : {e}")

    # 2. Affichage conditionnel selon si on est connecté ou non
    if "strava_token" not in st.session_state:
        # Pas encore connecté : on affiche le bouton HTML qui redirige vers Strava
        auth_url = get_strava_auth_url()
        st.markdown(f'<a href="{auth_url}" target="_self" style="display: inline-block; padding: 10px 20px; background-color: #FC4C02; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">🔗 Se connecter avec Strava</a>', unsafe_allow_html=True)
    
    else:
        # Connecté : On propose d'analyser les données
        st.success("✅ Connecté à ton compte Strava")
        
    if st.button("📊 Analyser ma dérive de fatigue", type="primary", use_container_width=True):
            with st.spinner("Récupération et analyse de tes sorties longues en cours..."):
                try:
                    runs = get_last_long_runs(st.session_state["strava_token"])
                    
                    if not runs:
                        st.warning("Aucune sortie de plus de 20km trouvée récemment dans ton historique.")
                    else:
                        st.write(f"🏃 **{len(runs)} sorties longues analysées**")
                            
                        # On récupère le taux ET les données pour le graphique
                        fatigue_rate, demo_run = analyze_fatigue_rate(st.session_state["strava_token"], runs)
                        
                        st.metric("Dérive de fatigue globale estimée", f"{fatigue_rate} % / 20km")
                        
                        # --- LE GRAPHIQUE D'EXPLICATION ---
                        if demo_run:
                            st.markdown("### 📈 Comment a-t-on calculé ça ?")
                            st.write(f"Exemple sur ta sortie : **{demo_run['name']}**")
                            
                            y_paces = demo_run['splits']
                            x_km = list(range(1, len(y_paces) + 1))
                            tiers = demo_run['tiers']
                            
                            fig = go.Figure()
                            
                            # La courbe de l'allure km par km
                            fig.add_trace(go.Scatter(
                                x=x_km, y=y_paces, mode='lines+markers', 
                                name='Allure (min/km)', line=dict(color='rgba(150, 150, 150, 0.5)', width=2)
                            ))
                            
                            # La ligne de moyenne du 1er tiers
                            fig.add_trace(go.Scatter(
                                x=[1, tiers], y=[demo_run['moy_debut'], demo_run['moy_debut']], 
                                mode='lines', name='Allure initiale (1er tiers)', 
                                line=dict(color='#28a745', width=4, dash='dash') # Vert
                            ))
                            
                            # La ligne de moyenne du dernier tiers
                            fig.add_trace(go.Scatter(
                                x=[len(x_km) - tiers + 1, len(x_km)], y=[demo_run['moy_fin'], demo_run['moy_fin']], 
                                mode='lines', name='Allure finale (Dernier tiers)', 
                                line=dict(color='#dc3545', width=4, dash='dash') # Rouge
                            ))
                            
                            # Mise en page du graphique
                            fig.update_layout(
                                xaxis_title="Kilomètres",
                                yaxis_title="Allure (min/km)",
                                yaxis=dict(autorange="reversed"), # On inverse l'axe (en course, un temps plus petit = plus rapide = plus haut)
                                margin=dict(l=0, r=0, t=30, b=0),
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Explication texte sous le graphique
                            st.info(f"""
                            💡 **Lecture de ta course :**\n
                            1️⃣ Sur le premier tiers, ton allure moyenne était de **{demo_run['moy_debut']:.2f} min/km**.\n
                            2️⃣ Sur le dernier tiers, la fatigue s'installant, ton allure est passée à **{demo_run['moy_fin']:.2f} min/km**.\n
                            📉 Cela représente une perte de vitesse brute de **+{demo_run['derive_brute']:.1f}%**. \n
                            🔄 L'algorithme a fait ce calcul sur toutes tes sorties, fait la moyenne, et l'a ramené sur une base de 20km pour l'adapter à l'application.
                            """)
                        
                        # Sauvegarde
                        os.makedirs("data", exist_ok=True)
                        profile["fatigue_rate"] = fatigue_rate
                        with open("data/runner_profile.json", "w") as f:
                            json.dump(profile, f)
                            
                        st.success("Taux de fatigue enregistré dans ton profil !")
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse : {e}")