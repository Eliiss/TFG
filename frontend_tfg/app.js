// 1. REEMPLAZA ESTA URL POR LA DE TU API GATEWAY EN AWS
const API_URL = "https://uza60pf6kd.execute-api.eu-south-2.amazonaws.com/predict";
const API_TIMEOUT_MS = 15000;
const RETRY_ATTEMPTS = 2;

// 2. Inicializar el mapa centrado en España
const map = L.map('map').setView([40.4168, -3.7038], 6);

// Añadir capa de mapa base sin API key
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19
}).addTo(map);

// 3. Función para dar color según el riesgo (De 0 a 100%)
function getColor(riesgo) {
    if (riesgo < 25) return "#4CAF50"; // Verde (Seguro)
    if (riesgo < 50) return "#FFC107"; // Amarillo (Precaución)
    if (riesgo < 75) return "#FF9800"; // Naranja (Alerta)
    return "#D32F2F";                  // Rojo (Peligro Extremo)
}

function esperar(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function fetchJsonConTimeout(url, options = {}, timeoutMs = API_TIMEOUT_MS) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
        const respuesta = await fetch(url, { ...options, signal: controller.signal });
        const raw = await respuesta.text();

        let datos = {};
        if (raw) {
            try {
                datos = JSON.parse(raw);
            } catch {
                datos = { raw };
            }
        }

        if (!respuesta.ok) {
            const detalle = datos.error || datos.message || raw || `HTTP ${respuesta.status}`;
            throw new Error(`Error API (${respuesta.status}): ${detalle}`);
        }

        return datos;
    } catch (error) {
        if (error.name === "AbortError") {
            throw new Error(`Timeout de ${Math.floor(timeoutMs / 1000)}s`);
        }
        throw error;
    } finally {
        clearTimeout(timeoutId);
    }
}

// 4. Obtener datos meteorológicos reales de Open-Meteo (gratuito, sin API key)
async function obtenerDatosMeteo(lat, lon) {
    const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}` +
        `&daily=precipitation_sum,temperature_2m_max,temperature_2m_min,wind_speed_10m_max` +
        `&past_days=14&forecast_days=1&timezone=Europe%2FMadrid`;

    const data = await fetchJsonConTimeout(url, { method: "GET" });

    if (!data.daily || !Array.isArray(data.daily.time) || data.daily.time.length === 0) {
        throw new Error("Open-Meteo devolvió datos incompletos");
    }

    const daily = data.daily;
    const n = daily.time.length;

    // Valores del día más reciente con datos completos
    const prec      = daily.precipitation_sum[n - 1] ?? 0;
    const tmin      = daily.temperature_2m_min[n - 1] ?? 15;
    const tmax      = daily.temperature_2m_max[n - 1] ?? 30;
    const velmedia  = daily.wind_speed_10m_max[n - 1] ?? 10;

    // Histórico de los 14 días previos para las ventanas temporales
    const precHist = daily.precipitation_sum.slice(0, n - 1).map(v => v ?? 0);
    const tmaxHist = daily.temperature_2m_max.slice(0, n - 1).map(v => v ?? 25);

    const sum = (arr, d) => arr.slice(-d).reduce((a, b) => a + b, 0);
    const avg = (arr, d) => sum(arr, d) / d;

    // Racha de días secos consecutivos
    let dry_streak = 0;
    for (let i = precHist.length - 1; i >= 0; i--) {
        if (precHist[i] <= 0.1) dry_streak++;
        else break;
    }

    return {
        prec, tmin, tmax, velmedia,
        // SAR (Sentinel-1): no disponible en tiempo real → valores representativos de verano seco
        VV_dB: -12.5, VH_dB: -18.0, VH_VV_Ratio: -5.5,
        dry_streak,
        // En entrenamiento se usaron medias móviles para precipitación y temperatura.
        prec_roll3:  avg(precHist, 3),  tmax_roll3:  avg(tmaxHist, 3),
        prec_roll7:  avg(precHist, 7),  tmax_roll7:  avg(tmaxHist, 7),
        prec_roll14: avg(precHist, 14), tmax_roll14: avg(tmaxHist, 14)
    };
}

// 5. Llamada a AWS Lambda con datos reales por provincia
async function consultarRiesgoAWS(provinciaNombre, capaPoligono) {
    document.getElementById('resultado-riesgo').innerText = "Calculando...";
    document.getElementById('mensaje-estado').innerText = "Obteniendo datos meteorológicos...";
    document.getElementById('mensaje-estado').style.backgroundColor = "#444";

    try {
        // Obtener centroide de la provincia a partir del polígono
        const center = capaPoligono.getBounds().getCenter();
        const payload = await obtenerDatosMeteo(center.lat, center.lng);
        payload.provincia = provinciaNombre;

        let datos = null;
        let ultimoError = null;

        for (let intento = 1; intento <= RETRY_ATTEMPTS; intento++) {
            try {
                document.getElementById('mensaje-estado').innerText =
                    intento === 1 ? "Conectando con AWS Lambda..." : `Reintentando conexión (${intento}/${RETRY_ATTEMPTS})...`;

                datos = await fetchJsonConTimeout(API_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (typeof datos.riesgo !== "number") {
                    throw new Error("La API no devolvió el campo numérico 'riesgo'");
                }

                break;
            } catch (error) {
                ultimoError = error;
                if (intento < RETRY_ATTEMPTS) {
                    await esperar(700);
                }
            }
        }

        if (!datos || typeof datos.riesgo !== "number") {
            throw ultimoError || new Error("No se pudo obtener respuesta válida de AWS");
        }

        // Lambda devuelve {"riesgo": 0.853} → lo convertimos a porcentaje
        const porcentajeRiesgo = datos.riesgo * 100;

        // Actualizamos la Interfaz
        document.getElementById('resultado-riesgo').innerText = porcentajeRiesgo.toFixed(1) + "%";
        document.getElementById('resultado-riesgo').style.color = getColor(porcentajeRiesgo);
        
        // Coloreamos la provincia en el mapa
        capaPoligono.setStyle({
            fillColor: getColor(porcentajeRiesgo),
            fillOpacity: 0.7,
            color: "#222",
            weight: 2
        });

        document.getElementById('mensaje-estado').innerText = "Predicción exitosa";
        document.getElementById('mensaje-estado').style.backgroundColor = getColor(porcentajeRiesgo);

    } catch (error) {
        console.error("Error en la petición a AWS:", error);
        document.getElementById('resultado-riesgo').innerText = "ERROR";
        const detalle = error && error.message ? String(error.message).slice(0, 120) : "Error no identificado";
        document.getElementById('mensaje-estado').innerText = `Fallo de conexión/API: ${detalle}`;
    }
}

// 6. Cargar las provincias de España (GeoJSON público)
const geojsonUrl = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/spain-provinces.geojson";

fetch(geojsonUrl)
    .then(res => res.json())
    .then(data => {
        L.geoJSON(data, {
            style: { color: "#666", weight: 1, fillColor: "#aaa", fillOpacity: 0.2 },
            onEachFeature: function(feature, layer) {
                // Evento al hacer clic en una provincia
                layer.on("click", function() {
                    const nombreProvincia = feature.properties.name;
                    document.getElementById('provincia-nombre').innerText = nombreProvincia;
                    
                    // Llamamos a AWS pasando la capa para que la coloree
                    consultarRiesgoAWS(nombreProvincia, layer);
                });
            }
        }).addTo(map);
    });