# ============================================================
# LANZAR NAVEGO COMMAND CENTER (DESDE EL PROYECTO)
# ============================================================

$proyecto = "C:\Users\ivan\Downloads\_Proyectos\NaveGoLocal"
$puerto = 8000
$archivoHtml = "dashboard\dashboard_command_center_v3.html"

Set-Location $proyecto

# Liberar puerto (usamos $proceso en lugar de $pid)
$proceso = netstat -ano | findstr ":$puerto" | ForEach-Object { ($_ -split ' ' | Where-Object {$_ -match '\d+$'})[-1] }
if ($proceso) {
    Stop-Process -Id $proceso -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Puerto $puerto liberado." -ForegroundColor Green
} else {
    Write-Host "✅ Puerto $puerto disponible." -ForegroundColor Green
}

# Abrir VS Code (opcional)
code $proyecto

# Levantar servidor
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:$puerto/")
$listener.Start()
Write-Host "✅ Servidor corriendo en http://localhost:$puerto/" -ForegroundColor Green
Write-Host "🔧 Endpoint /captura disponible" -ForegroundColor Magenta
Write-Host "⏹ Presiona Ctrl+C para detener" -ForegroundColor Gray

# Abrir navegador
Start-Process "http://localhost:$puerto/$archivoHtml"

# Bucle principal
while ($true) {
    try {
        $context = $listener.GetContext()
        $request = $context.Request
        $response = $context.Response
        $path = $request.Url.LocalPath

        if ($path -eq "/captura") {
            $scriptPath = Join-Path $PWD "captura.ps1"
            if (Test-Path $scriptPath) {
                $output = & $scriptPath 2>$null
                $response.ContentType = "application/json"
                $bytes = [System.Text.Encoding]::UTF8.GetBytes($output)
                $response.ContentLength64 = $bytes.Length
                $response.OutputStream.Write($bytes, 0, $bytes.Length)
            } else {
                $errorJson = "{ `"error`": `"captura.ps1 no encontrado`" }"
                $bytes = [System.Text.Encoding]::UTF8.GetBytes($errorJson)
                $response.ContentLength64 = $bytes.Length
                $response.OutputStream.Write($bytes, 0, $bytes.Length)
            }
            $response.OutputStream.Close()
            continue
        }

        if ($path -eq "/") { $path = "/$archivoHtml" }
        $filePath = Join-Path $PWD ($path.TrimStart('/')) -replace '/', '\'

        if (Test-Path $filePath -PathType Leaf) {
            $content = [System.IO.File]::ReadAllBytes($filePath)
            $response.ContentLength64 = $content.Length
            $response.OutputStream.Write($content, 0, $content.Length)
        } else {
            $response.StatusCode = 404
            $errorMsg = [System.Text.Encoding]::UTF8.GetBytes("404 Not Found: $path")
            $response.ContentLength64 = $errorMsg.Length
            $response.OutputStream.Write($errorMsg, 0, $errorMsg.Length)
        }
        $response.OutputStream.Close()

    } catch {
        Start-Sleep -Seconds 1
    }
}
