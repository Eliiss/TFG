# Inicia un servidor HTTP local para el frontend
# Necesario para evitar errores de CORS y bloqueos de Tracking Prevention
# cuando se abre index.html directamente como file://

$port = 8080
Write-Host "Iniciando servidor en http://localhost:$port"
Write-Host "Abre http://localhost:$port/index.html en tu navegador"
Write-Host "Pulsa Ctrl+C para detener el servidor"

Set-Location $PSScriptRoot
python -m http.server $port
