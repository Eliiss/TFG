import os
import pandas as pd
import numpy as np
import time
from dotenv import load_dotenv
from sentinelhub import SHConfig, SentinelHubStatistical, DataCollection, BBox, CRS

# --- CONFIGURACIÓN DE ENTORNO ---
ruta_actual = os.path.dirname(os.path.abspath(__file__))
ruta_env = os.path.join(ruta_actual, ".env")
load_dotenv(dotenv_path=ruta_env)

config = SHConfig()
config.sh_client_id = os.getenv("CDSE_CLIENT_ID")
config.sh_client_secret = os.getenv("CDSE_CLIENT_SECRET")
config.sh_base_url = 'https://sh.dataspace.copernicus.eu'
config.sh_token_url = 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'

# --- DICCIONARIO PARA DESCARGA MASIVA COMPLETA ---
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

# 1. Definición de la colección orientada a CDSE
S1_CDSE = DataCollection.SENTINEL1_IW.define_from("s1_cdse", service_url=config.sh_base_url)

# 2. EVALSCRIPT CORREGIDO (Sin duplicados)
evalscript = """
//VERSION=3
function setup() {
    return {
        input: [{
            bands: ["VV", "VH", "dataMask"]
        }],
        output: [
            { id: "VV", bands: 1, sampleType: "FLOAT32" },
            { id: "VH", bands: 1, sampleType: "FLOAT32" },
            { id: "dataMask", bands: 1, sampleType: "UINT8" }
        ]
    };
}

function evaluatePixel(sample) {
    return {
        VV: [sample.VV],
        VH: [sample.VH],
        dataMask: [sample.dataMask]
    };
}
"""

datos_satelite = []

# 3. BUCLE DE DESCARGA
for nombre, (lon, lat) in zonas.items():
    print(f"Descargando Radar Sentinel-1 (VV/VH) para {nombre}...")
    delta = 0.045
    bbox_coords = [lon - delta, lat - delta, lon + delta, lat + delta]
    bbox = BBox(bbox=bbox_coords, crs=CRS.WGS84)
    
    try:
        request = SentinelHubStatistical(
            aggregation=SentinelHubStatistical.aggregation(
                evalscript=evalscript, 
                time_interval=('2022-01-01', '2023-12-31'),
                aggregation_interval='P7D', # Semanal
                resolution=(0.0002, 0.0002) 
            ),
            input_data=[SentinelHubStatistical.input_data(S1_CDSE)],
            bbox=bbox, 
            config=config
        )
        
        response = request.get_data()[0]
        
        for dato in response['data']:
            stats_vv = dato['outputs']['VV']['bands']['B0']['stats']
            stats_vh = dato['outputs']['VH']['bands']['B0']['stats']
            
            if stats_vv['sampleCount'] > 0:
                datos_satelite.append({
                    'Zona': nombre,
                    'Fecha': dato['interval']['from'][:10],
                    'VV_linear': stats_vv['mean'],
                    'VH_linear': stats_vh['mean'],
                    'Píxeles_Válidos': stats_vv['sampleCount']
                })
        
        time.sleep(1) 
        print(f"-> {nombre} completado con éxito.")
        
    except Exception as e:
        print(f"❌ Error en zona {nombre}: {e}")
        continue

# 4. PROCESAMIENTO FINAL Y GUARDADO
if datos_satelite:
    df_sat = pd.DataFrame(datos_satelite)
    
    df_sat['VV_dB'] = 10 * np.log10(df_sat['VV_linear'].replace(0, np.nan))
    df_sat['VH_dB'] = 10 * np.log10(df_sat['VH_linear'].replace(0, np.nan))
    df_sat['VH_VV_Ratio'] = df_sat['VH_dB'] - df_sat['VV_dB']
    
    ruta_salida = os.path.join(os.getcwd(), 'features_sentinel1.csv')
    df_sat.to_csv(ruta_salida, index=False)
    
    print(f"\n========================================")
    print(f"Datos guardados en: {ruta_salida}")
    print(f"Total registros obtenidos: {len(df_sat)}")
    print(f"========================================")
    print(df_sat.head())
else:
    print("No se recuperaron datos de ninguna zona.")