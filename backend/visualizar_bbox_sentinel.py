"""Visualiza con Folium los BBox de Sentinel-1 usados en 02_copernicus_download.py."""
import folium

# Mismas zonas y mismo delta que en 02_copernicus_download.py
zonas = {
    'A CORUÑA': [-8.4065, 43.3623],
    'OURENSE': [-7.8633, 42.3358],
    'PONTEVEDRA': [-8.6444, 42.4310],
    'LUGO': [-7.5560, 43.0097],
    'ZAMORA': [-5.7463, 41.5030],
    'LEON': [-5.5703, 42.5987],
    'AVILA': [-4.6977, 40.6565],
    'SALAMANCA': [-5.6635, 40.9688],
    'SORIA': [-2.4631, 41.7636],
    'BURGOS': [-3.6969, 42.3440],
    'ALBACETE': [-1.8585, 38.9942],
    'CIUDAD REAL': [-3.9290, 38.9863],
    'CUENCA': [-2.1315, 40.0704],
    'GUADALAJARA': [-3.1622, 40.6329],
    'TOLEDO': [-4.0244, 39.8568],
    'VALENCIA': [-0.3763, 39.4699],
    'ALICANTE': [-0.4815, 38.3460],
    'CASTELLON': [-0.0513, 39.9864],
    'MADRID': [-3.7038, 40.4168],
    'CACERES': [-6.3722, 39.4743],
    'BADAJOZ': [-6.9706, 38.8779],
    'MURCIA': [-1.1300, 37.9870],
    'ALMERIA': [-2.4637, 36.8340],
    'CADIZ': [-6.2926, 36.5298],
    'CORDOBA': [-4.7728, 37.8882],
    'GRANADA': [-3.6067, 37.1773],
    'HUELVA': [-6.9504, 37.2664],
    'JAEN': [-3.7904, 37.7796],
    'MALAGA': [-4.4203, 36.7202],
    'SEVILLA': [-5.9732, 37.3828],
    'HUESCA': [-0.4087, 42.1362],
    'TERUEL': [-1.1069, 40.3457],
    'ZARAGOZA': [-0.8877, 41.6561],
    'ASTURIAS': [-5.8448, 43.3603],
    'BALEARES': [2.6502, 39.5694],
    'CANTABRIA': [-3.8044, 43.4623],
    'BARCELONA': [2.1734, 41.3851],
    'GIRONA': [2.8249, 41.9794],
    'LLEIDA': [0.6206, 41.6176],
    'TARRAGONA': [1.2445, 41.1187],
    'NAVARRA': [-1.6432, 42.8125],
    'ARABA/ALAVA': [-2.6725, 42.8467],
    'BIZKAIA': [-2.9350, 43.2630],
    'GIPUZKOA': [-1.9812, 43.3183],
    'LA RIOJA': [-2.4456, 42.4650]
}

DELTA = 0.045
ZONA_DESTACADA = "MADRID"

mapa = folium.Map(location=[40.0, -3.7], zoom_start=6, tiles="CartoDB positron")

for nombre, (lon, lat) in zonas.items():
    bounds = [[lat - DELTA, lon - DELTA], [lat + DELTA, lon + DELTA]]
    es_destacada = nombre == ZONA_DESTACADA

    folium.Rectangle(
        bounds=bounds,
        color="#D32F2F" if es_destacada else "#1976D2",
        weight=3 if es_destacada else 1,
        fill=True,
        fill_opacity=0.4 if es_destacada else 0.1,
        tooltip=f"{nombre} — BBox Sentinel-1 (±{DELTA}°)"
    ).add_to(mapa)

    folium.Marker(
        location=[lat, lon],
        popup=f"{nombre}<br>Centroide: ({lat}, {lon})",
        icon=folium.Icon(color="red" if es_destacada else "blue", icon="info-sign")
    ).add_to(mapa)

salida = "bbox_sentinel_mapa.html"
mapa.save(salida)
print(f"Mapa generado: {salida}")
