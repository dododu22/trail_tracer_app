# 🏃‍♂️ Ultra Pacer - Ton Jumeau Numérique de Trail

**Ultra Pacer** est une application intelligente d'aide à la performance pour le trail-running. Contrairement aux calculateurs classiques, elle crée un **Jumeau Numérique** basé sur tes capacités réelles (Index UTMB/ITRA) et ton historique Strava pour prédire ton allure kilomètre par kilomètre.

![Streamlit](https://img.shields.io/badge/Made%20with-Streamlit-FF4B4B?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![Strava](https://img.shields.io/badge/Strava-API-FC4C02?style=flat-square&logo=strava&logoColor=white)

## ✨ Fonctionnalités Clés

- **🧪 Jumeau Numérique Calibré :** Définition de ton profil via ton Index UTMB pour ajuster l'allure de base et la résistance au dénivelé.
- **🧡 Connexion Strava :** Analyse automatique de tes 5 dernières sorties longues pour calculer ta **dérive de fatigue réelle** (perte d'efficacité au fil des kilomètres).
- **🗺️ Tableau de Marche Dynamique :** Import de fichier GPX et génération de chronos de passage précis.
- **🌦️ Météo Intégrée :** Récupération des prévisions météo point par point (température, vent, ciel) pour chaque jalon de ta course.
- **💧 Stratégie de Nutrition :** Calcul automatique de l'hydratation (ajustée selon la météo) et du nombre de gels/portions nécessaires par tronçon.
- **⌚ Export Garmin "Up Ahead" :** Génération d'un fichier GPX enrichi. Ta montre Garmin te préviendra à chaque jalon avec la météo et les consignes de nutrition pour la suite.

## 🚀 Installation

1. **Cloner le projet :**
   ```bash
   git clone [https://github.com/ton-username/trail_tracer_app.git](https://github.com/ton-username/trail_tracer_app.git)
   cd trail_tracer_app