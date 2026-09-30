import json
import boto3
import os
import joblib
import pandas as pd

# Cliente S3 para bajar el modelo
s3 = boto3.client('s3')

# Variables (¡Asegúrate de que coincidan con tu bucket!)
BUCKET_NAME = 'tfg-elizabeth-2026'
MODEL_FILE = 'modelo_gradient_boosting.pkl'
COLS_FILE = 'columnas_modelo.pkl'

# AWS Lambda solo permite escribir en /tmp
LOCAL_MODEL_PATH = f'/tmp/{MODEL_FILE}'
LOCAL_COLS_PATH = f'/tmp/{COLS_FILE}'

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'POST, OPTIONS'
}

def lambda_handler(event, context):
    # Responder al preflight CORS (OPTIONS)
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': ''}

    try:
        # Descargar modelo si no está en caché
        if not os.path.exists(LOCAL_MODEL_PATH):
            s3.download_file(BUCKET_NAME, MODEL_FILE, LOCAL_MODEL_PATH)
            s3.download_file(BUCKET_NAME, COLS_FILE, LOCAL_COLS_PATH)
        
        modelo = joblib.load(LOCAL_MODEL_PATH)
        columnas = joblib.load(LOCAL_COLS_PATH)
        
        # Parsear input del usuario
        body = json.loads(event['body'])
        df = pd.DataFrame([body])[columnas]
        
        # Predicción
        prob = modelo.predict_proba(df)[0][1]
        
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({'riesgo': round(float(prob), 4)})
        }
    except Exception as e:
        return {'statusCode': 500, 'headers': CORS_HEADERS, 'body': json.dumps({'error': str(e)})}