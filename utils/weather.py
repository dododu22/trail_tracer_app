import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def get_weather_emoji(code):
    # (Ta fonction reste inchangée)
    if code == 0: return "☀️"
    elif code in [1, 2]: return "⛅"
    elif code in [3]: return "☁️"
    elif code in [45, 48]: return "🌫️"
    elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]: return "🌧️"
    elif code in [71, 73, 75, 77, 85, 86]: return "❄️"
    elif code in [95, 96, 99]: return "⛈️"
    return "🌡️"

@st.cache_data(show_spinner=False)
def fetch_weather_for_splits(df_splits_json):
    df = pd.read_json(df_splits_json)
    meteo_list = []
    
    # --- CONFIGURATION DU RETRY ---
    session = requests.Session()
    # On définit 3 tentatives avec un temps d'attente qui augmente entre chaque (backoff)
    retry_strategy = Retry(
        total=3,
        backoff_factor=0.5, # Attend 0.5s, 1s, 2s...
        status_forcelist=[429, 500, 502, 503, 504], # Réessaye si le serveur est surchargé
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)

    # --- UI : Barre de progression ---
    _, col_progress, _ = st.columns([1, 2, 1]) 
    with col_progress:
        progress_text = "Chargement météo..."
        my_bar = st.progress(0, text=progress_text)
    
    total_points = len(df)

    for index, row in df.iterrows():
        current_progress = (index + 1) / total_points
        my_bar.progress(current_progress, text=f"{progress_text} ({index + 1}/{total_points})")
        
        try:
            passage_dt = pd.to_datetime(row['datetime'])
            
            if passage_dt > datetime.now() + timedelta(days=14) or passage_dt < datetime.now() - timedelta(days=1):
                meteo_list.append("📅 > 14j")
                continue
                
            url = f"https://api.open-meteo.com/v1/forecast?latitude={row['lat']}&longitude={row['lon']}&hourly=temperature_2m,weathercode&timezone=auto"
            
            # Timeout réduit à 2 secondes comme demandé
            response_raw = session.get(url, timeout=2)
            response = response_raw.json()
            
            target_hour_str = passage_dt.replace(minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M")
            
            if 'hourly' in response and 'time' in response['hourly']:
                times = response['hourly']['time']
                if target_hour_str in times:
                    idx = times.index(target_hour_str)
                    temp = response['hourly']['temperature_2m'][idx]
                    code = response['hourly']['weathercode'][idx]
                    meteo_list.append(f"{get_weather_emoji(code)} {temp}°C")
                else:
                    meteo_list.append("N/A")
            else:
                meteo_list.append("N/A")
                
        except Exception:
            # Si après les retries et le timeout ça échoue encore, on ne bloque pas
            meteo_list.append("⚠️ N/A")
            
    my_bar.empty()
    df['Météo'] = meteo_list
    return df