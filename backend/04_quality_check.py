import os
import pandas as pd

def limpiar_y_verificar():
    ruta_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_maestro = os.path.join(ruta_actual, "dataset_TFG_VIYA_READY.csv")
    
    # 1. Cargar el dataset maestro
    df = pd.read_csv(ruta_maestro)
    df['fecha'] = pd.to_datetime(df['fecha'])
    
    print(f"Registros iniciales: {len(df)}")
    
    # 2. Filtrar para eliminar las zonas sin cobertura satelital (eliminar el año 2021)
    # Nos quedamos estrictamente con el rango donde tenemos Sentinel-1 cargado
    df_clean = df.dropna(subset=['VH_VV_Ratio']).copy()
    
    print(f"Registros tras eliminar filas sin satélite: {len(df_clean)}")
    
    # 3. Control de balance de incendios en el nuevo periodo
    n_incendios = df_clean['target_incendio'].sum()
    porcentaje = (n_incendios / len(df_clean)) * 100
    
    print("\n========================================")
    print("CHEQUEO DE CALIDAD PARA SAS VIYA")
    print("========================================")
    print(f"Rango temporal real: {df_clean['fecha'].min().strftime('%Y-%m-%d')} a {df_clean['fecha'].max().strftime('%Y-%m-%d')}")
    print(f"Total registros listos: {len(df_clean)}")
    print(f"Total incendios registrados: {n_incendios} ({porcentaje:.2f}%)")
    print(f"Nulos totales en el dataset: {df_clean.isnull().sum().sum()}")
    print("========================================")
    
    # 4. Guardar la versión definitiva
    ruta_final = os.path.join(ruta_actual, "dataset_TFG_VIYA_READY_CLEAN.csv")
    df_clean.to_csv(ruta_final, index=False)
    print(f"¡Dataset perfecto guardado en: {ruta_final}")

if __name__ == "__main__":
    limpiar_y_verificar()