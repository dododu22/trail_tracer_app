import streamlit as st 
import plotly.graph_objects as go
from streamlit_folium import st_folium
from utils.gpx_helper import create_map
import os
import pickle
from utils.biometrics import estimate_time_by_utmb_index
import json
from utils.export import generate_garmin_gpx


def render_map_section(df_gpx, df_splits):
    """Affiche la carte Folium"""
    st.subheader("🗺️ Parcours & Ravitaillements")
    m = create_map(df_gpx, df_splits=df_splits)
    st_folium(m, width="100%", height=450, returned_objects=[])


def render_table_section(df_gpx, df_splits):
    """Affiche le tableau de marche et les statistiques"""
    import streamlit as st
    
    st.markdown("---")
    st.subheader("⏱️ Tableau de marche détaillé")
    
    # Nettoyage des colonnes techniques (lat, lon, datetime) pour l'affichage
    cols_to_drop = [col for col in ['lat', 'lon', 'datetime'] if col in df_splits.columns]
    df_display = df_splits.drop(columns=cols_to_drop)
    
    st.dataframe(df_display, use_container_width=True)
    
    # --- CALCUL DES TOTAUX ---
    dist_totale = df_gpx['distance_km'].max()
    dplus_total = df_gpx['cum_d_plus'].max()
    
    # NOUVEAU : On récupère le temps de la dernière ligne (.iloc[-1])
    temps_total_course = df_splits['Temps total'].iloc[-1]
    
    # On ajoute le temps estimé à la phrase de base
    caption_text = f"🏁 Distance : **{dist_totale:.1f} km** | ⛰️ D+ : **{dplus_total:.0f} m** | ⏱️ Temps estimé : **{temps_total_course}**"
    
    # Vérification si la stratégie nutritionnelle est active
    if 'Nutrition' in df_splits.columns and 'Hydratation' in df_splits.columns:
        total_portions = 0
        total_flasques = 0.0
        
        # Extraction et somme des portions de nourriture
        for item in df_splits['Nutrition']:
            if item != "-":
                try:
                    total_portions += int(item.split(' ')[1])
                except Exception:
                    pass
                    
        # Extraction et somme des flasques d'eau
        for item in df_splits['Hydratation']:
            if item != "-":
                try:
                    total_flasques += float(item.split(' ')[1])
                except Exception:
                    pass
                    
        caption_text += f" | ⚡ Nutrition : **{total_portions} portions** | 💧 Eau : **{total_flasques:.1f} flasques**"
        
    st.caption(caption_text)
    
    if os.path.exists("data/runner_profile.json"):
        with open("data/runner_profile.json", "r") as f:
            profil_coureur = json.load(f)
            
        itra_score = profil_coureur.get("itra_score")
        if itra_score:
            # On calcule le temps global UTMB
            h_utmb, m_utmb, temps_decimal_utmb = estimate_time_by_utmb_index(dist_totale, dplus_total, itra_score)
            temps_utmb_str = f"{h_utmb:02d}:{m_utmb:02d}:00"
            
            # On récupère le temps calculé par le Pacer
            import pandas as pd
            temps_pacer_td = pd.to_timedelta(temps_total_course)
            temps_pacer_decimal = temps_pacer_td.total_seconds() / 3600.0
            
            # Calcul de l'écart
            ecart_minutes = (temps_pacer_decimal - temps_decimal_utmb) * 60
            
            st.markdown("---")
            st.markdown(f"### ⚖️ Reality Check (Index {itra_score})")
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Temps Pacer (Ton plan)", temps_total_course)
            with col_b:
                st.metric("Temps Statistique (UTMB)", temps_utmb_str)
            with col_c:
                if abs(ecart_minutes) < 15:
                    st.metric("Écart", "Parfaitement calibré", delta="0 min", delta_color="off")
                elif ecart_minutes > 0:
                    st.metric("Écart", f"Plan plus lent", delta=f"+{int(ecart_minutes)} min", delta_color="inverse")
                else:
                    st.metric("Écart", f"Plan plus rapide", delta=f"{int(ecart_minutes)} min", delta_color="normal")
                
            st.info("💡 **Comment lire ceci ?** Si ton plan Pacer est beaucoup plus rapide que le Temps UTMB, tu as peut-être été trop optimiste sur ton *Allure de base* ou ta *Dérive de fatigue*. S'il est plus lent, tu t'es gardé une bonne marge de sécurité !")
            
    return df_splits


def render_export_and_save(df_gpx, df_splits_complet, settings, uploaded_file, projet_charge):
    """Affiche les boutons d'export CSV, Garmin et de sauvegarde Pickle"""
    st.markdown("---")
    st.subheader("💾 Export & Sauvegarde")
    
    col_dl1, col_dl2, col_dl3 = st.columns(3)
    
    nom_fichier_original = projet_charge.get("nom_fichier", "projet_inconnu.gpx") if projet_charge else (uploaded_file.name if uploaded_file else "Course")
    nom_base = nom_fichier_original.replace(".gpx", "")
    
    # --- BOUTON 1 : CSV ---
    with col_dl1:
        # On supprime lat, lon et datetime UNIQUEMENT pour le tableur CSV
        cols_to_drop = [col for col in ['lat', 'lon', 'datetime'] if col in df_splits_complet.columns]
        df_csv = df_splits_complet.drop(columns=cols_to_drop)
        
        csv = df_csv.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📊 Télécharger Tableau (CSV)",
            data=csv,
            file_name=f"Plan_{nom_base}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
    # --- BOUTON 2 : GARMIN (Le Jumeau Numérique Embarqué) ---
    with col_dl2:
        try:
            # Garmin reçoit maintenant les données complètes avec les coordonnées !
            gpx_data = generate_garmin_gpx(df_gpx, df_splits_complet)
            
            st.download_button(
                label="⌚ Exporter pour Garmin (.gpx)",
                data=gpx_data,
                file_name=f"Garmin_Plan_{nom_base}.gpx",
                mime="application/gpx+xml",
                use_container_width=True,
                type="primary"
            )
        except Exception as e:
            st.error(f"Erreur export Garmin: {e}")
            
    # --- BOUTON 3 : SAUVEGARDE PROJET (Pickle) ---
    with col_dl3:
        if st.button("💾 Sauvegarder le Projet", use_container_width=True):
            os.makedirs("data", exist_ok=True)
            
            save_data = {
                "nom_fichier": nom_fichier_original,
                "df_gpx": df_gpx, 
                **settings 
            }
            
            file_path = f"data/projet_{nom_base}.pkl"
            
            with open(file_path, "wb") as f:
                pickle.dump(save_data, f)
            
            st.success(f"Sauvegardé : `{file_path}`")
            
    st.caption("💡 **Astuce Garmin :** Importe le fichier `.gpx` téléchargé dans *Garmin Connect (Entraînement et planification > Parcours > Créer un parcours > Importer)*. Les informations de météo et d'hydratation apparaîtront comme des points 'Up Ahead' (Sur l'itinéraire) sur ta montre.")


def render_elevation_profile(df_gpx, df_splits):
    """Génère le profil altimétrique interactif avec Plotly"""
    import streamlit as st # Au cas où il manque en haut du fichier
    
    st.markdown("---")
    st.subheader("📈 Profil Altimétrique")

    fig = go.Figure()

    # 1. La zone de la montagne (Remplissage sous la courbe)
    fig.add_trace(go.Scatter(
        x=df_gpx['distance_km'],
        y=df_gpx['elevation'],
        fill='tozeroy',
        mode='lines',
        line=dict(color='#FF4B4B', width=2),
        fillcolor='rgba(255, 75, 75, 0.1)',
        name='Profil',
        hoverinfo='skip' # On désactive le survol sur la montagne elle-même pour ne pas surcharger
    ))

    # 2. Préparation des données pour les marqueurs
    # (On reconvertit en float car le tableau les avait mis en texte formaté)
    x_markers = df_splits['Km'].astype(float)
    y_markers = df_splits['Altitude (m)'].astype(float)
    types = df_splits['Type']
    passages = df_splits['Passage']
    
    # Intégration de la météo si elle est calculée
    meteos = df_splits['Météo'] if 'Météo' in df_splits.columns else [""] * len(df_splits)

    # 3. Création des infobulles personnalisées
    hover_texts = []
    for t, x, y, p, m in zip(types, x_markers, y_markers, passages, meteos):
        meteo_text = f"<br>🌤️ Météo: {m}" if m else ""
        hover_texts.append(f"<b>{t}</b><br>Km {x} - Alt: {y}m<br>⏱️ Passage: {p}{meteo_text}")

    # 4. Stylisation des marqueurs (Bleu=Ravito, Vert=Arrivée, Gris=Jalon)
    marker_colors = ['#1E90FF' if 'Ravito' in t else '#32CD32' if 'Arrivée' in t else '#888888' for t in types]
    marker_sizes = [12 if 'Ravito' in t else 14 if 'Arrivée' in t else 6 for t in types]
    marker_symbols = ['diamond' if 'Ravito' in t else 'star' if 'Arrivée' in t else 'circle' for t in types]

    # 5. Ajout des marqueurs sur la courbe
    fig.add_trace(go.Scatter(
        x=x_markers,
        y=y_markers,
        mode='markers',
        marker=dict(
            color=marker_colors, 
            size=marker_sizes, 
            symbol=marker_symbols,
            line=dict(color='white', width=1)
        ),
        text=hover_texts,
        hoverinfo='text',
        name='Points de passage'
    ))

    # 6. Mise en page du graphique
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis_title="Distance (km)",
        yaxis_title="Altitude (m)",
        hovermode="closest",
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
    )

    st.plotly_chart(fig, use_container_width=True)