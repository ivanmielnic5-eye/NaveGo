# NaveGo Estado
$path = "PROJECT_STATE.md"
if (-not (Test-Path $path)) { Write-Host "No se encontro PROJECT_STATE.md" -ForegroundColor Red; exit }
$lineas = Get-Content $path
foreach ($linea in $lineas) {
    if ($linea.StartsWith("##")) { Write-Host $linea -ForegroundColor Cyan }
    elseif ($linea.StartsWith("-")) { Write-Host $linea -ForegroundColor Green }
    else { Write-Host $linea }
}
