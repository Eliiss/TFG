import pandas as pd
import numpy as np

print("Iniciando Ingeniería de Características (Feature Engineering)...")

# 1. Cargar el dataset base
# Asegúrate de que el archivo base se llame así o cambia el nombre aquí
df = pd.read_csv('datos_base.csv')

# 2. Asegurar que las fechas son formato datetime y ordenar
df['fecha'] = pd.to_datetime(df['fecha'])
df = df.sort_values(by=['provincia', 'fecha']).reset_index(drop=True)

# 3. Eliminar 'tmed' para evitar colinealidad (como dijimos en el TFG)
if 'tmed' in df.columns:
    df = df.drop(columns=['tmed'])
    print("- Columna 'tmed' eliminada por colinealidad.")

# 4. Crear el contador de Racha Seca (dry_streak)
print("- Calculando Racha de Días Secos (dry_streak)...")
# Creamos una columna booleana: 1 si es seco (<= 0.1 mm), 0 si llueve
df['is_dry'] = (df['prec'] <= 0.1).astype(int)
df['dry_streak'] = 0

# Iteramos para sumar días secos consecutivos
for idx in range(1, len(df)):
    # Solo sumamos si seguimos en la misma provincia
    if df.loc[idx, 'provincia'] == df.loc[idx - 1, 'provincia']:
        if df.loc[idx, 'is_dry'] == 1:
            if df.loc[idx - 1, 'is_dry'] == 1:
                df.loc[idx, 'dry_streak'] = df.loc[idx - 1, 'dry_streak'] + 1
            else:
                df.loc[idx, 'dry_streak'] = 1
        else:
            df.loc[idx, 'dry_streak'] = 0
    else:
        # Si cambiamos de provincia, reiniciamos el contador si es un día seco
        df.loc[idx, 'dry_streak'] = 1 if df.loc[idx, 'is_dry'] == 1 else 0

# Ya no necesitamos la columna is_dry
df = df.drop(columns=['is_dry'])

# 5. Crear Medias Móviles Temporales (Rolling Windows) CON PROTECCIÓN DE DATA LEAKAGE
print("- Calculando Medias Móviles con protección de Data Leakage (.shift(1))...")
ventanas = [3, 7, 14]

for window in ventanas:
    # Precipitación
    col_prec = f'prec_roll{window}'
    df[col_prec] = df.groupby('provincia')['prec'].shift(1).rolling(window=window, min_periods=1).mean()
    
    # Temperatura Máxima
    col_tmax = f'tmax_roll{window}'
    df[col_tmax] = df.groupby('provincia')['tmax'].shift(1).rolling(window=window, min_periods=1).mean()

# 6. Eliminar nulos generados por el shift/rolling al principio de cada serie
df_final = df.dropna().reset_index(drop=True)

# 7. Guardar el dataset final listo para SAS Viya
output_name = 'dataset_TFG_VIYA_READY_CLEAN.csv'
df_final.to_csv(output_name, index=False)

print("\n=======================================================")
print(f"✅ FEATURE ENGINEERING COMPLETADO CON ÉXITO")
print(f"Archivo generado: {output_name}")
print(f"Total de registros: {len(df_final)}")
print(f"Columnas resultantes: {list(df_final.columns)}")
print("=======================================================")        