# Forest Fire Risk Prediction System

> Visual Interface: https://eliiss.github.io/TFG/frontend_tfg/

End-to-end system for the analysis and prediction of forest fire risk in Spain, combining meteorological data, historical fire records, and Earth observation through Sentinel-1.

![Conceptual view of the system](https://img.shields.io/badge/TFG-AI%20%7C%20Data%20%7C%20Cloud-1f6feb?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![XGBoost](https://img.shields.io/badge/Model-XGBoost-EA4335?style=flat-square)
![AWS Lambda](https://img.shields.io/badge/Deployment-AWS%20Lambda-FF9900?style=flat-square&logo=awslambda&logoColor=white)

## The project at a glance

Forest fires depend on the interaction between meteorological conditions, accumulated dryness, and vegetation status. This project transforms these signals into a probability of fire risk to support proactive decision-making.

**The central idea:** integrate heterogeneous data, build temporal variables without data leakage, train a model for an imbalanced problem, and make inference available through both a web interface and a serverless API.

### Key results

| Aspect | Result |
| --- | --- |
| Model | XGBoost / Gradient Boosting |
| ROC-AUC metric | 0.8348 |
| Recall | 76% |
| Prediction | Probability between 0 and 1 |
| Interface | Interactive provincial map |
| Cloud architecture | API Gateway + AWS Lambda + Amazon S3 + Docker |

> The probability shown is a model prediction, not confirmation that a fire exists. The system is intended as a decision-support tool and does not replace official emergency services.

## Architecture

```mermaid
flowchart LR
    A[AEMET\nMeteorology] --> B[ETL and cleaning]
    C[MITECO\nHistorical fires] --> B
    D[Copernicus Sentinel-1\nVV / VH] --> E[Data fusion]
    B --> E
    E --> F[Feature engineering\nDry spells and rolling windows]
    F --> G[Final dataset]
    G --> H[XGBoost\nTraining and evaluation]
    H --> I[Serialized model]
    I --> J[Amazon S3]
    J --> K[AWS Lambda\nInference]
    K --> L[API Gateway]
    L --> M[Frontend HTML + Leaflet]
    N[Open-Meteo\nDemo data] --> M
```

## Data flow

1. **Meteorological and historical ETL:** AEMET data are cleaned and aggregated by province and date, and days with fires recorded by MITECO are labeled.
2. **Satellite observation:** radar images from Sentinel-1 are queried through the Copernicus Data Space Ecosystem, and the `VV`, `VH`, and `VH/VV` signals are calculated.
3. **Fusion:** meteorological and satellite sources are merged by province and date, imputing missing observations using the most recent available value.
4. **Feature engineering:** dry spells and rolling means of precipitation and temperature are calculated for 3-, 7-, and 14-day windows. These windows use only information available prior to the target date to avoid leakage.
5. **Training:** XGBoost learns to distinguish fire and non-fire days. `scale_pos_weight` compensates for class imbalance without generating synthetic observations.
6. **Inference:** Lambda downloads the model from S3, receives variables over HTTP, and returns the estimated probability.

## Web demo

The interface allows the user to select a province in Spain and check its fire risk level. The color represents the probability returned by the API:

- Green: low risk, below 25%.
- Yellow: caution, between 25% and 50%.
- Orange: alert, between 50% and 75%.
- Red: high risk, 75% or more.

The demo obtains recent meteorological data from [Open-Meteo](https://open-meteo.com/). To maintain interactivity, the web version uses representative values for the variables required by the model.

## Repository structure

```text
.
├──
└── backend
    ├── 01_etl_aemet_miteco.py       # Construction of the labeled meteorological dataset
    ├── 02_copernicus_download.py    # Download and transformation of Sentinel-1
    ├── cruce.py                     # Fusion of meteorological and satellite information
    ├── 04_quality_check.py          # Quality control and final filtering
    ├── 05_feature_engineering.py    # Temporal variables for the model
    ├── 06_train.py                 # Training, evaluation, and export
├── frontend_tfg/               # Web interface with Leaflet
└── lambda_container/           # Container for AWS Lambda
```

## Installation and local usage

### 1. Prepare the environment

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r .requirements.txt
```

The requirements file contains the libraries used during analysis, satellite downloads, modeling, and visualization.

### 2. Run the pipeline

The scripts must be executed from the repository root in the following order:

```powershell
python 01_etl_aemet_miteco.py
python 02_copernicus_download.py
python cruce.py
python 04_quality_check.py
python 05_feature_engineering.py
python 06_train.py
```

Downloading Copernicus data requires credentials in a local `.env` file:

```env
CDSE_CLIENT_ID=your_client_id
CDSE_CLIENT_SECRET=your_client_secret
```

Never publish this file or any credentials in the repository.

### 3. Run the interface

The interface must be served over HTTP to allow external requests. On Windows:

```powershell
cd frontend_tfg
.\start_server.ps1
```

Then open [http://localhost:8080](http://localhost:8080). The API URL configured in `frontend_tfg/app.js` points to the AWS-deployed API. To use another API, replace `API_URL` with your desired value.

## Serverless deployment

The `lambda_container/` directory contains the inference container:

- Official AWS Lambda base image for Python 3.11.
- Dependencies installed as binaries to reduce compatibility issues.
- Model and feature list downloaded from Amazon S3 during execution.
- JSON response with the `riesgo` field.

Example request body expected by the function:

```json
{
  "prec": 0.0,
  "tmin": 18.2,
  "tmax": 34.5,
  "velmedia": 22.0,
  "VV_dB": -12.5,
  "VH_dB": -18.0,
  "VH_VV_Ratio": -5.5,
  "dry_streak": 8,
  "prec_roll3": 0.2,
  "tmax_roll3": 31.4,
  "prec_roll7": 1.1,
  "tmax_roll7": 30.8,
  "prec_roll14": 4.6,
  "tmax_roll14": 29.9
}
```

Example response:

```json
{
  "riesgo": 0.853
}
```

## Technologies

**Data and science:** Python, pandas, NumPy, scikit-learn, XGBoost, AEMET, MITECO, Copernicus Sentinel-1.

**Cloud and MLOps:** Docker, AWS Lambda, Amazon S3, Amazon ECR, API Gateway.

**Frontend:** HTML, CSS, JavaScript, Leaflet.js, OpenStreetMap, Open-Meteo.

## Limitations and next steps

- Incorporate updated Sentinel-1 observations directly into demo inference.
- Validate the model with temporal and geographic partitions to better assess generalization capability.
- Add monitoring for predictions, latency, and data drift in AWS.
- Automate dataset and model updates through a CI/CD pipeline.
- Version datasets and models with experiment traceability.

## Author

**Elizabeth**

Final Degree Project on forest fire risk prediction using artificial intelligence, satellite data, and cloud architecture.

If this project is useful to you or you would like to know more technical details, you can open an issue or contact me through my GitHub profile.


# Sistema de predicción de riesgo de incendios forestales

> Interfaz Visual https://eliiss.github.io/TFG/frontend_tfg/

Sistema end-to-end de análisis y predicción de incendios forestales en España que combina datos meteorológicos, registros históricos de incendios y observación terrestre mediante Sentinel-1.

![Vista conceptual del sistema](https://img.shields.io/badge/TFG-IA%20%7C%20Datos%20%7C%20Cloud-1f6feb?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![XGBoost](https://img.shields.io/badge/Modelo-XGBoost-EA4335?style=flat-square)
![AWS Lambda](https://img.shields.io/badge/Despliegue-AWS%20Lambda-FF9900?style=flat-square&logo=awslambda&logoColor=white)

## El proyecto en una mirada

Los incendios forestales dependen de la interacción entre condiciones meteorológicas, sequedad acumulada y estado de la vegetación. Este proyecto transforma esas señales en una probabilidad de riesgo de incendio para apoyar la toma de decisiones de forma proactiva.

**La idea central:** integrar datos heterogéneos, construir variables temporales sin fuga de información, entrenar un modelo para un problema desbalanceado y poner la inferencia a disposición de una interfaz web y una API serverless.

### Resultados destacados

| Aspecto | Resultado |
| --- | --- |
| Modelo | XGBoost / Gradient Boosting |
| Métrica ROC-AUC | 0.8348 |
| Recall | 76% |
| Predicción | Probabilidad entre 0 y 1 |
| Interfaz | Mapa interactivo por provincias |
| Arquitectura cloud | API Gateway + AWS Lambda + Amazon S3 + Docker |

> La probabilidad mostrada es una predicción del modelo, no una confirmación de que exista un incendio. El sistema está pensado como apoyo a la decisión y no sustituye a los servicios oficiales de emergencia.

## Arquitectura

```mermaid
flowchart LR
    A[AEMET\nMeteorología] --> B[ETL y limpieza]
    C[MITECO\nIncendios históricos] --> B
    D[Copernicus Sentinel-1\nVV / VH] --> E[Fusión de datos]
    B --> E
    E --> F[Feature engineering\nRachas y ventanas móviles]
    F --> G[Dataset final]
    G --> H[XGBoost\nEntrenamiento y evaluación]
    H --> I[Modelo serializado]
    I --> J[Amazon S3]
    J --> K[AWS Lambda\nInferencia]
    K --> L[API Gateway]
    L --> M[Frontend HTML + Leaflet]
    N[Open-Meteo\nDatos de la demo] --> M
```

## Flujo de datos

1. **ETL meteorológico e histórico:** se limpian y agregan los datos de AEMET por provincia y fecha, y se etiquetan los días con incendios registrados por MITECO.
2. **Observación satelital:** se consultan imágenes radar Sentinel-1 a través de Copernicus Data Space Ecosystem y se calculan las señales `VV`, `VH` y el ratio `VH/VV`.
3. **Fusión:** se unen las fuentes meteorológica y satelital por provincia y fecha, imputando los pasos sin observación mediante el último valor disponible.
4. **Ingeniería de características:** se calculan la racha seca y medias móviles de precipitación y temperatura para ventanas de 3, 7 y 14 días. Las ventanas usan únicamente información previa a la fecha objetivo para evitar fugas de información.
5. **Entrenamiento:** XGBoost aprende a distinguir días con y sin incendio. `scale_pos_weight` compensa el desbalanceo de clases sin generar observaciones sintéticas.
6. **Inferencia:** Lambda descarga el modelo desde S3, recibe las variables por HTTP y devuelve la probabilidad estimada.

## Demo web

La interfaz permite seleccionar una provincia sobre un mapa de España y consultar su nivel de riesgo. El color representa la probabilidad devuelta por la API:

- Verde: riesgo bajo, menos del 25%.
- Amarillo: precaución, entre el 25% y el 50%.
- Naranja: alerta, entre el 50% y el 75%.
- Rojo: riesgo alto, 75% o más.

La demo obtiene la meteorología reciente desde [Open-Meteo](https://open-meteo.com/). Para mantener la experiencia interactiva, la versión web utiliza valores representativos para las variables necesarias del modelo.

## Estructura del repositorio

```text
.
├──
└── backend
    ├── 01_etl_aemet_miteco.py       # Construcción del dataset meteorológico etiquetado
    ├── 02_copernicus_download.py    # Descarga y transformación de Sentinel-1
    ├── cruce.py                     # Fusión de meteorología e información satelital
    ├── 04_quality_check.py          # Control de calidad y filtrado final
    ├── 05_feature_engineering.py    # Variables temporales para el modelo
    ├── 06_train.py                  # Entrenamiento, evaluación y exportación
├── frontend_tfg/               # Interfaz web con Leaflet
└── lambda_container/           # Contenedor para AWS Lambda
```
## Instalación y uso local

### 1. Preparar el entorno

```bash
python -m venv .venv
```

En Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r .requirements.txt
```

El fichero de requisitos contiene las librerías utilizadas durante el análisis, la descarga satelital, el modelado y la visualización.

### 2. Ejecutar el pipeline

Los scripts deben ejecutarse desde la raíz del repositorio y en este orden:

```powershell
python 01_etl_aemet_miteco.py
python 02_copernicus_download.py
python cruce.py
python 04_quality_check.py
python 05_feature_engineering.py
python 06_train.py
```

La descarga de Copernicus requiere credenciales en un fichero `.env` local:

```env
CDSE_CLIENT_ID=tu_client_id
CDSE_CLIENT_SECRET=tu_client_secret
```

No publiques nunca ese fichero ni credenciales en el repositorio.

### 3. Ejecutar la interfaz

La interfaz necesita servirse por HTTP para permitir las peticiones externas. En Windows:

```powershell
cd frontend_tfg
.\start_server.ps1
```

Después, abre [http://localhost:8080](http://localhost:8080). La URL de API configurada en `frontend_tfg/app.js` apunta a la API desplegada en AWS; para utilizar otra, sustituye `API_URL` por tu valor deseado.

## Despliegue serverless

El directorio `lambda_container/` contiene el contenedor de inferencia:

- Imagen base oficial de AWS Lambda para Python 3.11.
- Dependencias instaladas como binarios para reducir problemas de compatibilidad.
- Modelo y lista de columnas descargados desde Amazon S3 durante la ejecución.
- Respuesta JSON con el campo `riesgo`.

Ejemplo de cuerpo esperado por la función:

```json
{
  "prec": 0.0,
  "tmin": 18.2,
  "tmax": 34.5,
  "velmedia": 22.0,
  "VV_dB": -12.5,
  "VH_dB": -18.0,
  "VH_VV_Ratio": -5.5,
  "dry_streak": 8,
  "prec_roll3": 0.2,
  "tmax_roll3": 31.4,
  "prec_roll7": 1.1,
  "tmax_roll7": 30.8,
  "prec_roll14": 4.6,
  "tmax_roll14": 29.9
}
```

Respuesta:

```json
{
  "riesgo": 0.853
}
```

## Tecnologías

**Datos y ciencia:** Python, pandas, NumPy, scikit-learn, XGBoost, AEMET, MITECO, Copernicus Sentinel-1.

**Cloud y MLOps:** Docker, AWS Lambda, Amazon S3, Amazon ECR, API Gateway.

**Frontend:** HTML, CSS, JavaScript, Leaflet.js, OpenStreetMap y Open-Meteo.

## Limitaciones y siguientes pasos

- Incorporar observaciones Sentinel-1 actualizadas directamente en la inferencia de la demo.
- Validar el modelo con particiones temporales y geográficas para medir mejor su capacidad de generalización.
- Añadir monitorización de predicciones, latencia y deriva de datos en AWS.
- Automatizar la actualización del dataset y del modelo mediante un pipeline CI/CD.
- Versionar datasets y modelos con trazabilidad de experimentos.

## Autor

**Elizabeth**

Trabajo de Fin de Grado sobre predicción de riesgo de incendios forestales mediante inteligencia artificial, datos satelitales y arquitectura cloud.

Si este proyecto te resulta útil o quieres conocer más detalles técnicos, puedes abrir una issue o contactar conmigo a través de mi perfil de GitHub.
