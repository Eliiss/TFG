import pandas as pd
import numpy as np

def limpiar_texto(txt):
    if pd.isna(txt): return txt
    return str(txt).strip().upper()

def crear_dataset():
    # 1. CARGAR MITECO (Excel)
    print("Cargando datos de MITECO (Excel)...")
    file_miteco = "miteco_Xlsx_20260301_202445_1.xlsx"
    df_miteco = pd.read_excel(file_miteco, sheet_name='Informe')
    
    # Extraer la fecha de la columna 'Detectado'
    # Intentamos convertir a datetime (ignora errores de hora si los hay)
    df_miteco['fecha'] = pd.to_datetime(df_miteco['Detectado'], errors='coerce').dt.date
    df_miteco['provincia'] = df_miteco['Provincia'].apply(limpiar_texto)
    df_miteco['target_incendio'] = 1
    
    # Nos quedamos con lo esencial y quitamos duplicados (1 incendio por día/provincia)
    miteco_clean = df_miteco[['fecha', 'provincia', 'target_incendio']].dropna()
    miteco_clean = miteco_clean.drop_duplicates(subset=['fecha', 'provincia'])
    
    print(f"-> MITECO cargado: {len(miteco_clean)} eventos de incendio.")

    # 2. CARGAR AEMET (CSV)
    print("\nCargando datos de AEMET (CSV)...")
    file_aemet = "aemet_historico_2021_2025.csv"
    df_aemet = pd.read_csv(file_aemet, dtype=str)
    
    # Convertir fecha
    df_aemet['fecha'] = pd.to_datetime(df_aemet['fecha']).dt.date
    df_aemet['provincia'] = df_aemet['provincia'].apply(limpiar_texto)
    
    # Limpiar columnas numéricas (Comas -> Puntos)
    cols_num = ['tmed', 'prec', 'tmin', 'tmax', 'velmedia']
    for col in cols_num:
        print(f"   Limpiando columna: {col}")
        df_aemet[col] = df_aemet[col].str.replace(',', '.').astype(float)
    
    # Agrupar por provincia/fecha para tener la media meteorológica provincial
    aemet_provincial = df_aemet.groupby(['fecha', 'provincia'])[cols_num].mean().reset_index()
    print(f"-> AEMET cargado: {len(aemet_provincial)} registros diarios por provincia.")

    # 3. CRUCE DE DATOS (Merge)
    print("\nRealizando el cruce final...")
    # La base es AEMET (todos los días) y le pegamos MITECO (solo días con fuego)
    df_final = pd.merge(aemet_provincial, miteco_clean, on=['fecha', 'provincia'], how='left')
    
    # Rellenar los días sin fuego con 0
    df_final['target_incendio'] = df_final['target_incendio'].fillna(0).astype(int)

    # 4. FILTRO TEMPORAL Y LIMPIEZA
    # Cortamos en la fecha máxima de AEMET (16 de abril 2024)
    fecha_limite = pd.to_datetime("2024-04-16").date()
    df_final = df_final[df_final['fecha'] <= fecha_limite]
    
    # Ordenar por fecha
    df_final = df_final.sort_values(by=['fecha', 'provincia'])

    # 5. GUARDAR Y RESUMEN
    output_file = "dataset_TFG_FINAL_LIMPIO.csv"
    df_final.to_csv(output_file, index=False)
    
    print(f"\n{'='*40}")
    print(f"¡DATASET GENERADO CON ÉXITO!")
    print(f"Archivo: {output_file}")
    print(f"Rango: {df_final['fecha'].min()} a {df_final['fecha'].max()}")
    print(f"Total registros: {len(df_final)}")
    print(f"Total incendios (1): {df_final['target_incendio'].sum()}")
    print(f"Días sin incendio (0): {(df_final['target_incendio'] == 0).sum()}")
    print(f"Viento (velmedia) con datos: {df_final['velmedia'].notnull().sum()}")
    print(f"{'='*40}")

if __name__ == "__main__":
    crear_dataset()