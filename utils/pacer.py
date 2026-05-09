import pandas as pd
from datetime import datetime, timedelta, date

import json
import os


def calculate_fatigue_multiplier(distance_actuelle_km, fatigue_rate_percent, fatigue_interval_km):
    blocs = distance_actuelle_km / fatigue_interval_km
    taux_decimal = fatigue_rate_percent / 100.0
    return (1 + taux_decimal) ** blocs

def generate_splits(df, base_pace, penalty_dplus, start_time, race_date, interval_km=10, fatigue_rate=5.0, fatigue_interval=20, custom_ravitos_km=None):
    # Combinaison de la date et de l'heure de départ
    dt_depart = datetime.combine(race_date, start_time)
    
    splits = []
    
    lat_depart = df.iloc[0]['lat']
    lon_depart = df.iloc[0]['lon']
    alt_depart = int(df.iloc[0]['elevation'])
    
    splits.append({
        "Type": "Départ",
        "Km": "0.0",
        "Altitude (m)": f"{alt_depart:.0f}",
        "D+ (Tronçon)": "+0",
        "Fatigue": "+0.0%",
        "Allure": "-",
        "Temps total": "0:00:00", 
        "Passage": dt_depart.strftime("%H:%M"),
        "datetime": dt_depart.isoformat(), # On le met au format texte comme les autres
        "lat": float(lat_depart),
        "lon": float(lon_depart)
    })
    # ----------------------------------------------------

    
    if custom_ravitos_km is None:
        custom_ravitos_km = []
        
    max_km = df['distance_km'].max()
    
    points_cibles = list(range(interval_km, int(max_km) + interval_km, interval_km))
    points_cibles.extend(custom_ravitos_km)
    points_cibles.append(max_km)
    
    # Sécurisation : on force le nettoyage et on rejette tout ce qui dépasse strictement le max_km
    points_cibles = sorted(list(set([round(float(p), 1) for p in points_cibles if float(p) <= max_km])))
    
    if round(max_km, 1) not in points_cibles:
        points_cibles.append(round(max_km, 1))
        points_cibles.sort()

    minutes_cumulees = 0.0
    dist_precedente = 0.0
    dplus_precedent = 0.0
    
    for target_km in points_cibles:
        # SÉCURITÉ : On cherche l'index le plus proche, puis on s'assure qu'on le trouve bien dans le DataFrame
        try:
            idx = (df['distance_km'] - target_km).abs().idxmin()
            point = df.loc[idx]
        except (ValueError, KeyError):
            # Si pour une raison quelconque pandas ne trouve pas de point, on passe au suivant
            continue
        
        dist_actuelle = point['distance_km']
        dplus_actuel = point['cum_d_plus']
        
        delta_dist = dist_actuelle - dist_precedente
        delta_dplus = dplus_actuel - dplus_precedent
        
        if delta_dist < 0.1 and dist_actuelle > 0.5:
            continue

        eta = datetime.combine(race_date, start_time) + timedelta(minutes=minutes_cumulees)
        temps_course_str = str(timedelta(minutes=round(minutes_cumulees)))
            
        milieu_troncon = dist_precedente + (delta_dist / 2)
        facteur_fatigue = calculate_fatigue_multiplier(milieu_troncon, fatigue_rate, fatigue_interval)
        
        temps_troncon_theorique = (delta_dist * base_pace) + ((delta_dplus / 100) * penalty_dplus)
        temps_troncon_reel = temps_troncon_theorique * facteur_fatigue
        minutes_cumulees += temps_troncon_reel
        
        eta = datetime.combine(date.today(), start_time) + timedelta(minutes=minutes_cumulees)
        temps_course_str = str(timedelta(minutes=round(minutes_cumulees)))
        
        allure_troncon = temps_troncon_reel / delta_dist if delta_dist > 0 else 0
        minutes_allure = int(allure_troncon)
        secondes_allure = int((allure_troncon - minutes_allure) * 60)
        allure_str = f"{minutes_allure}:{secondes_allure:02d}/km"
        
        if round(dist_actuelle, 1) >= round(max_km - 0.1, 1): # Tolérance pour l'arrivée
            type_point = "🏁 Arrivée"
        elif any(round(dist_actuelle, 1) == round(r, 1) for r in custom_ravitos_km):
            type_point = "🚰 Ravito"
        else:
            type_point = "📍 Jalon"
        
        # SÉCURITÉ : On s'assure que lat et lon sont bien des floats valides pour Folium
        splits.append({
            "Type": type_point,
            "Km": f"{dist_actuelle:.1f}",
            "Altitude (m)": f"{point['elevation']:.0f}",
            "D+ (Tronçon)": f"+{delta_dplus:.0f}",
            "Fatigue": f"+{((facteur_fatigue - 1) * 100):.1f}%",
            "Allure": allure_str,
            "Temps total": temps_course_str,
            "Passage": eta.strftime("%H:%M"),
            "datetime": eta.isoformat(), # NOUVEAU : On stocke la date complète pour la météo
            "lat": float(point['lat']),
            "lon": float(point['lon'])
        })
        
        dist_precedente = dist_actuelle
        dplus_precedent = dplus_actuel
        
    return pd.DataFrame(splits)



def apply_nutrition_strategy(df_splits):
    """Calcule le nombre de flasques et de gels nécessaires par tronçon"""
    
    if not os.path.exists("data/nutrition_profile.json"):
        return df_splits
        
    with open("data/nutrition_profile.json", "r") as f:
        nutri = json.load(f)
        
    # --- LA CORRECTION EST ICI ---
    # On convertit directement la colonne "Temps total" en heures décimales
    # (Pandas gère nativement le format "1:30:00" très bien sans qu'on y touche)
    temps_cumule_heures = pd.to_timedelta(df_splits['Temps total']).dt.total_seconds() / 3600.0
    
    # La durée d'un tronçon est la différence avec le jalon précédent.
    # Pour le 1er jalon (index 0) qui donne "NaN", on le remplit avec son propre temps total !
    durees_heures = temps_cumule_heures.diff().fillna(temps_cumule_heures.iloc[0])
    
    eau_str_list = []
    bouffe_str_list = []
    
    for idx, duree_h in enumerate(durees_heures):
        row = df_splits.iloc[idx]
        
        # S'il y a un point ultra-proche (ex: un ravito à 200m d'un jalon régulier), on ignore
        if duree_h <= 0.05: 
            eau_str_list.append("-")
            bouffe_str_list.append("-")
            continue

        # Calcul Glucides
        besoin_carbs_g = duree_h * nutri["carbs_h"]
        nb_gels = max(1, round(besoin_carbs_g / nutri["gel_carbs"]))
        bouffe_str_list.append(f"⚡ {nb_gels} portions")
        
        # Calcul Eau
        besoin_eau_ml = duree_h * nutri["water_h"]
        
        # Modification Eau vs Météo
        meteo_val = str(row.get('Météo', ''))
        if '°C' in meteo_val:
            try:
                temp = float(meteo_val.split(' ')[-1].replace('°C', ''))
                if temp > 22.0:
                    besoin_eau_ml *= 1.25 # On augmente de 25%
            except:
                pass
                
        nb_flasques = round(besoin_eau_ml / nutri["flask_vol"], 1)
        eau_str_list.append(f"💧 {nb_flasques} flsq")
        
    df_splits['Hydratation'] = eau_str_list
    df_splits['Nutrition'] = bouffe_str_list
    
    return df_splits