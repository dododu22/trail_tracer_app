import streamlit as st
from streamlit_option_menu import option_menu

def render_navbar():
    """Affiche la barre de navigation et gère le routage intelligent (Strava)"""
    
    # --- 1. ROUTAGE & MÉMOIRE ---
    tabs = ["Course", "Nutrition", "Réglages"]
    
    # Interception du retour de Strava (présence de '?code=' dans l'URL)
    if "code" in st.query_params:
        st.session_state["active_tab"] = "Réglages"
        
    # Initialisation de la mémoire au premier lancement
    elif "active_tab" not in st.session_state:
        st.session_state["active_tab"] = "Course"
        
    # On trouve le numéro de l'onglet actif (0, 1 ou 2)
    try:
        current_index = tabs.index(st.session_state["active_tab"])
    except ValueError:
        current_index = 0

    # --- 2. AFFICHAGE DU MENU ---
    selected = option_menu(
        menu_title=None, 
        options=tabs,
        icons=["map", "apple", "gear"],
        default_index=current_index,  # C'est ICI que la magie opère !
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#1E1E1E", "border-radius": "10px"},
            "icon": {"color": "#FAFAFA", "font-size": "18px"}, 
            "nav-link": {"font-size": "15px", "text-align": "center", "margin":"5px", "padding": "10px", "border-radius": "8px"},
            "nav-link-selected": {"background-color": "#FF4B4B", "font-weight": "bold"},
        }
    )
    
    # --- 3. SAUVEGARDE ---
    # Si l'utilisateur clique manuellement sur un autre onglet, on le mémorise
    st.session_state["active_tab"] = selected

    st.markdown("---")
    return selected