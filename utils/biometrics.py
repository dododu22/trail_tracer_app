import pandas as pd
import numpy as np

def get_coeffs_from_score(score, vitesse_ref_1000=14.5):
    """
    Traduit un score ITRA/UTMB (0-1000) en coefficients d'allure.
    Basé sur la véritable équation du Km-Effort UTMB.
    """
    if score <= 0: 
        return 10.0, 15.0 # Valeurs de sécurité si score invalide
    
    # 1. Calcul de la vitesse du coureur (en km-Effort / heure)
    vitesse_coureur = vitesse_ref_1000 * (score / 1000.0)
    
    if vitesse_coureur <= 0:
        return 10.0, 15.0
        
    # 2. Temps moyen en minutes pour parcourir 1 km-Effort
    # Ex: Si vitesse = 10 km-E/h, allure = 6.0 min/km-E
    allure_km_e = 60.0 / vitesse_coureur
    
    # 3. Répartition physiologique (Plat vs Montée)
    # Dans le modèle UTMB pur, base_pace = penalty_dplus. 
    # En réalité, on court un peu plus vite sur le plat (x0.85) 
    # et la montée pure coûte un peu plus cher (x1.15)
    base_pace = allure_km_e * 0.85
    penalty_dplus = allure_km_e * 1.15
    
    return round(base_pace, 2), round(penalty_dplus, 2)


def estimate_time_by_utmb_index(distance_km, dplus_m, itra_score, vitesse_ref_1000=14.5):
    """
    Calcule le temps de course global estimé selon la formule officielle du Km-Effort UTMB.
    """
    # Calcul du Kilomètre-Effort (1km + 100m d+)
    km_effort = distance_km + (dplus_m / 100.0)
    
    # Vitesse proportionnelle au score du coureur
    vitesse_coureur = vitesse_ref_1000 * (itra_score / 1000.0)
    
    # Sécurité division par zéro
    if vitesse_coureur <= 0:
        return 0, 0, 0.0
        
    # Temps total en heures
    temps_heures = km_effort / vitesse_coureur
    
    # Conversion en heures/minutes (ex: 12.5 -> 12h30)
    heures = int(temps_heures)
    minutes = int((temps_heures - heures) * 60)
    
    return heures, minutes, temps_heures