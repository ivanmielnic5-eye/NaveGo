# NaveGo Backup Script
Set-Location "C:\Users\ivan\Downloads\_Proyectos\NaveGoLocal"

$fecha = Get-Date -Format "yyyy-MM-dd-HHmm"
$backupDir = "C:\Users\ivan\Downloads\_Backups\NaveGoLocal_backup_$fecha"

Write-Host "=== NaveGo: Creando backup ===" -ForegroundColor Cyan
Write-Host "Destino: $backupDir" -ForegroundColor Yellow

# 1. Copia de seguridad completa (sin node_modules ni .expo)
Copy-Item -Path "C:\Users\ivan\Downloads\_Proyectos\NaveGoLocal" -Destination $backupDir -Recurse -Exclude @('node_modules','.expo')
Write-Host "Backup creado." -ForegroundColor Green

# 2. Commit automático en Git
Write-Host "Guardando versión en Git..." -ForegroundColor Yellow
git add .
git commit -m "backup $fecha"
Write-Host "Commit hecho." -ForegroundColor Green

Write-Host "=== NaveGo: Backup completo ===" -ForegroundColor Cyan