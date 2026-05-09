import folium

def process_gpx(gpx_string):
    import gpxpy
    import pandas as pd
    
    """Parse le GPX et retourne un DataFrame avec distances et D+"""
    gpx = gpxpy.parse(gpx_string)
    
    data = []
    for point_data in gpx.get_points_data():
        point = point_data.point
        data.append({
            "lat": float(point.latitude),   # Forcé en float natif
            "lon": float(point.longitude),  # Forcé en float natif
            "elevation": point.elevation,
            "distance_m": point_data.distance_from_start
        })
        
    df = pd.DataFrame(data)
    df['distance_km'] = df['distance_m'] / 1000
    
    df['ele_diff'] = df['elevation'].diff()
    df['d_plus'] = df['ele_diff'].apply(lambda x: x if x > 0 else 0)
    df['cum_d_plus'] = df['d_plus'].cumsum()
    
    return df


def create_map(df_gpx, df_splits=None):
    """Génère la carte avec icônes météo et métadonnées complètes au survol"""
    # 1. Initialisation
    coords = [[float(lat), float(lon)] for lat, lon in zip(df_gpx['lat'], df_gpx['lon'])]
    m = folium.Map(location=coords[0], zoom_start=11)
    
    # 2. Injection du CSS FontAwesome pour garantir l'affichage des icônes
    header = '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">'
    m.get_root().header.add_child(folium.Element(header))

    # 3. Tracé de la trace GPX
    folium.PolyLine(coords, color="#FF4B4B", weight=3, opacity=0.8).add_to(m)
    
    # Correspondance Emoji -> FontAwesome 4.7
    weather_icon_map = {
        "☀️": "sun-o",
        "⛅": "cloud",
        "☁️": "cloud",
        "🌧️": "tint",
        "❄️": "snowflake-o",
        "⛈️": "bolt",
        "🌫️": "align-justify"
    }

    if df_splits is not None:
        for _, row in df_splits.iterrows():
            type_str = str(row.get('Type', ''))
            meteo_str = str(row.get('Météo', ''))
            
            # Détermination de l'icône et de la couleur
            icon_name = "info-circle"
            color = "orange"
            
            if "Ravito" in type_str:
                icon_name = "cutlery"
                color = "blue"
            elif "Arrivée" in type_str:
                icon_name = "flag-checkered"
                color = "green"
            elif "Départ" in type_str:
                icon_name = "play"
                color = "purple"
            else:
                for emoji, fa_name in weather_icon_map.items():
                    if emoji in meteo_str:
                        icon_name = fa_name
                        break

            # 4. RECONSTRUCTION DU TOOLTIP AVEC METADONNÉES
            # On utilise du HTML pour un rendu propre
            tooltip_html = f"""
            <div style="font-family: 'Helvetica', sans-serif; min-width: 150px;">
                <h4 style="margin: 0 0 5px 0; color: #FF4B4B;">{type_str}</h4>
                <table style="width: 100%; font-size: 12px; border-collapse: collapse;">
                    <tr><td><b>Distance:</b></td><td style="text-align: right;">{row['Km']} km</td></tr>
                    <tr><td><b>Altitude:</b></td><td style="text-align: right;">{row['Altitude (m)']} m</td></tr>
                    <tr><td><b>Passage:</b></td><td style="text-align: right; color: blue;"><b>{row['Passage']}</b></td></tr>
                    <tr><td><b>Allure:</b></td><td style="text-align: right;">{row['Allure']}</td></tr>
                    <tr><td><b>Météo:</b></td><td style="text-align: right;">{meteo_str}</td></tr>
                </table>
            </div>
            """

            folium.Marker(
                location=[float(row['lat']), float(row['lon'])],
                icon=folium.Icon(color=color, icon=icon_name, prefix='fa'),
                tooltip=folium.Tooltip(tooltip_html, sticky=False)
            ).add_to(m)
            
    m.fit_bounds(m.get_bounds())
    return m