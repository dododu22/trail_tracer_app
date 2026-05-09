import gpxpy
import gpxpy.gpx

def generate_garmin_gpx(df_gpx, df_splits):
    """
    Génère un fichier GPX avec la trace GPS et injecte les splits 
    comme des Waypoints avec instructions pour la montre Garmin.
    """
    gpx = gpxpy.gpx.GPX()

    # 1. On recrée la trace (La ligne sur la carte)
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx_track.name = "Ultra Pacer - Plan de course"
    gpx.tracks.append(gpx_track)
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    # On remet tous les points d'origine
    for _, row in df_gpx.iterrows():
        gpx_segment.points.append(
            gpxpy.gpx.GPXTrackPoint(row['lat'], row['lon'], elevation=row['elevation'])
        )

    # 2. On crée les Waypoints (Les alertes pop-up sur la montre)
    for i in range(len(df_splits)):
        row = df_splits.iloc[i]
        
        type_pt = str(row['Type'])
        km = row['Km']
        
        # On nettoie les emojis pour le titre car certaines montres ne les lisent pas bien
        clean_type = type_pt.replace('🚰 ', '').replace('📍 ', '').replace('🏁 ', '').replace('▶️ ', '')
        titre = f"Km{km} {clean_type}"
        
        # Logique pour la description (Le texte qui s'affiche sous le titre)
        if i < len(df_splits) - 1:
            next_row = df_splits.iloc[i+1]
            meteo_next = str(next_row.get('Météo', ''))
            eau_next = str(next_row.get('Hydratation', '-'))
            
            # Format ultra-compact pour écran de montre
            if "Ravito" in type_pt or "Départ" in type_pt:
                # Au ravito, la priorité absolue c'est de dire combien remplir pour la suite
                desc = f"Remplir: {eau_next} | Météo next: {meteo_next}"
            else:
                # Sur un jalon normal, on donne un aperçu de la suite
                desc = f"Allure: {row['Allure']} | Next: {meteo_next}"
        else:
            desc = "Ligne d'arrivée !."

        # Création du point d'alerte
        wpt = gpxpy.gpx.GPXWaypoint(
            latitude=row['lat'], 
            longitude=row['lon'], 
            name=titre,
            description=desc
        )
        # On peut forcer le type pour que Garmin lui donne une belle icône interne
        if "Ravito" in type_pt:
            wpt.type = "Aid Station"
            wpt.symbol = "Drinking Water"
            
        gpx.waypoints.append(wpt)

    return gpx.to_xml()