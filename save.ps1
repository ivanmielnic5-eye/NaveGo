# NaveGo Save Script
Set-Location "C:\Users\ivan\Downloads\_Proyectos\NaveGoLocal"

$fecha = Get-Date -Format "yyyy-MM-dd-HHmm"
$mensaje = "version $fecha"

Write-Host "Guardando versión: $mensaje" -ForegroundColor Cyan

git add .
git commit -m $mensaje

Write-Host "=== NaveGo: Versión guardada ===" -ForegroundColor Green