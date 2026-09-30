import os
import pandas as pd
import joblib
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score

def entrenar_modelo_final():
    ruta_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_datos = os.path.join(ruta_actual, "dataset_TFG_VIYA_READY_CLEAN.csv")
    
    print("1. Cargando el dataset maestro...")
    df = pd.read_csv(ruta_datos)
    
    # 2. Separar variables (Features) y objetivo (Target)
    # Quitamos columnas que no sirven para predecir (fecha, provincia, target)
    X = df.drop(columns=['fecha', 'provincia', 'target_incendio'])
    y = df['target_incendio']
    
    # 3. Dividir en entrenamiento (80%) y test (20%)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # 4. Calcular el peso para balancear las clases (Lo que hacía SAS con el Event-Based Sampling)
    # Ratio = (Días sin incendio) / (Días con incendio)
    ratio_desbalanceo = len(y_train[y_train == 0]) / len(y_train[y_train == 1])
    
    print(f"2. Entrenando el modelo XGBoost (Gradient Boosting) con scale_pos_weight={ratio_desbalanceo:.2f}...")
    
    # Creamos el modelo replicando el Gradient Boosting de SAS
    modelo = XGBClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        scale_pos_weight=ratio_desbalanceo, # ¡Aquí solucionamos el desbalanceo!
        random_state=42,
        eval_metric='auc'
    )
    
    modelo.fit(X_train, y_train)
    
    # 5. Evaluación rápida para confirmar que va como un tiro
    y_pred = modelo.predict(X_test)
    y_proba = modelo.predict_proba(X_test)[:, 1]
    
    print("\n--- RESULTADOS DEL MODELO LOCAL ---")
    print(classification_report(y_test, y_pred))
    print(f"ROC-AUC Score: {roc_auc_score(y_test, y_proba):.4f}")
    print("-----------------------------------\n")
    
    # 6. Exportar el modelo para AWS
    ruta_modelo = os.path.join(ruta_actual, 'modelo_gradient_boosting.pkl')
    joblib.dump(modelo, ruta_modelo)
    
    # Exportar también la lista exacta de columnas que espera el modelo (vital para la Lambda)
    ruta_columnas = os.path.join(ruta_actual, 'columnas_modelo.pkl')
    joblib.dump(list(X.columns), ruta_columnas)
    
    print(f"3. ¡Modelo guardado con éxito en: {ruta_modelo}!")

if __name__ == "__main__":
    entrenar_modelo_final()