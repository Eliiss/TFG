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
