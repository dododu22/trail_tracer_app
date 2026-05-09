import requests
import pandas as pd
import streamlit as st

# Récupération des secrets depuis le fichier .streamlit/secrets.toml
CLIENT_ID = st.secrets["strava"]["client_id"]
CLIENT_SECRET = st.secrets["strava"]["client_secret"]
REDIRECT_URI = st.secrets["strava"]["redirect_uri"]

def get_strava_auth_url():
    """Génère l'URL pour le bouton de connexion Strava"""
    return f"https://www.strava.com/oauth/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&approval_prompt=force&scope=activity:read_all"

def exchange_code_for_token(code):
    """Échange le code de retour contre un token d'accès officiel"""
    url = "https://www.strava.com/oauth/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code"
    }
    response = requests.post(url, data=payload)
    return response.json()

def get_last_long_runs(access_token, min_distance_km=20, limit=10):
    """Récupère les dernières sorties longues"""
    url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"per_page": 100} # On regarde les 30 dernières
    
    response = requests.get(url, headers=headers, params=params)
    activities = response.json()
    
    long_runs = []
    for act in activities:
        if act.get('type') == 'Run' and act.get('distance', 0) >= (min_distance_km * 1000):
            long_runs.append(act)
            if len(long_runs) >= limit:
                break
                
    return long_runs

def get_activity_splits(access_token, activity_id):
    """Récupère les détails d'une activité pour avoir les temps kilomètre par kilomètre."""
    url = f"https://www.strava.com/api/v3/activities/{activity_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('splits_metric', [])
    return []

def analyze_fatigue_rate(access_token, long_runs):
    """
    Analyse de dérive avec extraction des données pour le graphique explicatif.
    """
    if not long_runs:
        return 5.0, None # On retourne une valeur par défaut et "None" pour le graphique
        
    fatigue_scores = []
    demo_run = None
    max_dist = 0
    
    for run in long_runs:
        splits = get_activity_splits(access_token, run['id'])
        valid_splits = [s for s in splits if s.get('distance', 0) > 900]
        
        if len(valid_splits) < 15: 
            continue
            
        tiers = len(valid_splits) // 3
        
        allures_debut = [(s['moving_time'] / 60) for s in valid_splits[:tiers]]
        allure_moy_debut = sum(allures_debut) / len(allures_debut)
        
        allures_fin = [(s['moving_time'] / 60) for s in valid_splits[-tiers:]]
        allure_moy_fin = sum(allures_fin) / len(allures_fin)
        
        if allure_moy_debut > 0:
            derive_pct = ((allure_moy_fin - allure_moy_debut) / allure_moy_debut) * 100
            distance_totale = len(valid_splits)
            derive_standardisee = derive_pct * (20.0 / distance_totale)
            
            fatigue_scores.append(max(0, derive_standardisee))
            
            # --- NOUVEAU : On sauvegarde les données de la plus longue course pour le graphique ---
            if distance_totale > max_dist:
                max_dist = distance_totale
                demo_run = {
                    "name": run['name'],
                    "splits": [s['moving_time'] / 60 for s in valid_splits], # Les allures de chaque km
                    "tiers": tiers,
                    "moy_debut": allure_moy_debut,
                    "moy_fin": allure_moy_fin,
                    "derive_brute": derive_pct
                }
        
    if not fatigue_scores:
        return 5.0, None
        
    average_fatigue = sum(fatigue_scores) / len(fatigue_scores)
    final_rate = min(15.0, max(2.0, round(average_fatigue, 1)))
    
    return final_rate, demo_run # On renvoie les DEUX variables