# NaveGo Start Script
Write-Host "=== NaveGo: Iniciando sistema ===" -ForegroundColor Cyan

# Limpiar puerto 3000
Write-Host "Limpiando puerto 3000..." -ForegroundColor Yellow
$connection = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue
if ($connection) {
    Stop-Process -Id $connection.OwningProcess -Force
    Write-Host "Puerto 3000 liberado." -ForegroundColor Green
} else {
    Write-Host "Puerto 3000 libre." -ForegroundColor Green
}

# Levantar servidor local
Write-Host "Levantando servidor local..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd "C:\Users\ivan\Downloads\NaveGoLocal"; node simulate.js'

# Levantar túnel
Write-Host "Levantando túnel..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd "C:\Users\ivan\Downloads\NaveGoLocal"; npx localtunnel --port 3000'

# Levantar Metro
Write-Host "Levantando Metro..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd "C:\Users\ivan\Downloads\NaveGoLocal"; npx expo start --clear'

Write-Host "=== NaveGo: Todo en marcha ===" -ForegroundColor Cyan