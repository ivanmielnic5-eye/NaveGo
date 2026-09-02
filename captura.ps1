# ============================================================
# CAPTURA DE ESTADO DEL SISTEMA (Godot 4.7.1)
# ============================================================

# Procesos que más memoria usan (top 5)
$topProcesos = Get-Process | Sort-Object -Property WorkingSet -Descending | Select-Object -First 5

# Memoria total
try {
    $memTotal = (Get-CimInstance -ClassName Win32_ComputerSystem -ErrorAction Stop).TotalPhysicalMemory / 1MB
} catch {
    $memTotal = 0
}

# Memoria disponible
try {
    $memDisponible = (Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction Stop).FreePhysicalMemory / 1MB
} catch {
    $memDisponible = 0
}

# Estado de Godot (cualquier proceso que contenga "Godot" en el nombre)
$godotProcs = Get-Process | Where-Object { $_.ProcessName -like "*Godot*" } -ErrorAction SilentlyContinue
$godotRunning = if ($godotProcs) { "✅ Sí" } else { "❌ No" }

# Archivos modificados hoy
$proyecto = "C:\Users\ivan\Downloads\_Proyectos\NaveGoLocal"
$archivosHoy = Get-ChildItem -Path $proyecto -Recurse -File -ErrorAction SilentlyContinue | 
               Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-24) } | 
               Select-Object -First 10 -Property Name, LastWriteTime

# Construir objeto JSON
$data = @{
    timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    cpu = 0
    memoria = @{
        disponible = [math]::Round($memDisponible, 0)
        total = [math]::Round($memTotal, 0)
        porcentaje = if ($memTotal -gt 0) { [math]::Round((($memTotal - $memDisponible) / $memTotal) * 100, 1) } else { 0 }
    }
    godot = $godotRunning
    procesos = $topProcesos | ForEach-Object { @{ nombre = $_.ProcessName; memoria = [math]::Round($_.WorkingSet / 1MB, 1) } }
    archivos_recientes = $archivosHoy | ForEach-Object { @{ nombre = $_.Name; modificado = $_.LastWriteTime.ToString("HH:mm") } }
}

# Devolver JSON
$data | ConvertTo-Json -Depth 3
