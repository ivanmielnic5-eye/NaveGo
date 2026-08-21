# NaveGo Save Script con integridad SHA-256
Set-Location "C:\Users\ivan\Downloads\_Proyectos\NaveGoLocal"

$fecha = Get-Date -Format "yyyy-MM-dd-HHmm"
$hash = (Get-FileHash -Algorithm SHA256 "save.ps1").Hash

# Actualizar integrity.json
$integrity = @{
  "save.ps1" = $hash
  "start.ps1" = (Get-FileHash -Algorithm SHA256 "start.ps1").Hash
  "backup.ps1" = (Get-FileHash -Algorithm SHA256 "backup.ps1").Hash
  "estado.ps1" = (Get-FileHash -Algorithm SHA256 "estado.ps1").Hash
  "voice_bridge.js" = (Get-FileHash -Algorithm SHA256 "voice_bridge.js").Hash
  "simulate.js" = (Get-FileHash -Algorithm SHA256 "simulate.js").Hash
}
$integrity | ConvertTo-Json | Set-Content -Path "integrity.json" -Encoding UTF8

$mensaje = "version $fecha - hash $($hash.Substring(0,12))"
Write-Host "Guardando version: $fecha" -ForegroundColor Cyan
Write-Host "Hash save.ps1: $($hash.Substring(0,12))" -ForegroundColor Yellow

git add .
git commit -m $mensaje

Write-Host "=== NaveGo: Version guardada con integridad ===" -ForegroundColor Green
