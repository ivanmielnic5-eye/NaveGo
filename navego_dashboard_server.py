#!/usr/bin/env python3
"""
NaveGo Dashboard Server — Puerto 8080
Sirve el dashboard HTML y provee el endpoint /captura con datos del sistema Linux.
Reemplaza a captura.ps1 (Windows) en Linux.
"""

import http.server
import socketserver
import json
import os
import subprocess
import time
from datetime import datetime

PORT = 8080
DASHBOARD_DIR = os.path.expanduser("~/navego_recuperado")
PROYECTO = os.path.expanduser("~/navego_recuperado")


def get_memoria():
    try:
        with open("/proc/meminfo") as f:
            info = {}
            for line in f:
                parts = line.split(":")
                if len(parts) == 2:
                    info[parts[0].strip()] = parts[1].strip().split()[0]
        total_kb = int(info.get("MemTotal", 0))
        avail_kb = int(info.get("MemAvailable", 0))
        total_mb = total_kb // 1024
        avail_mb = avail_kb // 1024
        usado_pct = round(((total_mb - avail_mb) / total_mb) * 100, 1) if total_mb else 0
        return {
            "disponible": avail_mb,
            "total": total_mb,
            "porcentaje": usado_pct
        }
    except Exception:
        return {"disponible": 0, "total": 0, "porcentaje": 0}


def get_cpu():
    try:
        with open("/proc/loadavg") as f:
            load = float(f.read().split()[0])
        return round(load * 100 / os.cpu_count(), 1) if os.cpu_count() else 0
    except Exception:
        return 0


def get_godot():
    try:
        result = subprocess.run(
            ["pgrep", "-if", "godot"],
            capture_output=True, text=True, timeout=2
        )
        return "✅ Sí" if result.returncode == 0 else "❌ No"
    except Exception:
        return "❌ No"


def get_procesos():
    try:
        result = subprocess.run(
            ["ps", "-eo", "comm,rss", "--sort=-rss"],
            capture_output=True, text=True, timeout=2
        )
        lines = result.stdout.strip().split("\n")[1:6]
        procesos = []
        for line in lines:
            parts = line.split(None, 1)
            if len(parts) == 2:
                nombre = parts[0]
                memoria_mb = round(int(parts[1]) / 1024, 1)
                procesos.append({"nombre": nombre, "memoria": memoria_mb})
        return procesos
    except Exception:
        return []


def get_archivos_recientes():
    try:
        ahora = time.time()
        hace_24h = ahora - (24 * 3600)
        archivos = []
        for root, dirs, files in os.walk(PROYECTO):
            dirs[:] = [d for d in dirs if d not in ("node_modules", ".git", "android", ".expo")]
            for f in files:
                path = os.path.join(root, f)
                try:
                    mtime = os.path.getmtime(path)
                    if mtime > hace_24h:
                        archivos.append({
                            "nombre": f,
                            "modificado": datetime.fromtimestamp(mtime).strftime("%H:%M"),
                            "_mtime": mtime
                        })
                except Exception:
                    pass
        archivos.sort(key=lambda x: x["_mtime"], reverse=True)
        for a in archivos:
            del a["_mtime"]
        return archivos[:10]
    except Exception:
        return []


def build_captura():
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cpu": get_cpu(),
        "memoria": get_memoria(),
        "godot": get_godot(),
        "procesos": get_procesos(),
        "archivos_recientes": get_archivos_recientes()
    }


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DASHBOARD_DIR, **kwargs)

    def do_GET(self):
        if self.path.startswith("/captura"):
            data = build_captura()
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    os.chdir(DASHBOARD_DIR)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"[NAVEGO DASHBOARD] Servidor activo en http://localhost:{PORT}")
        print(f"[NAVEGO DASHBOARD] Dashboard: http://localhost:{PORT}/dashboard/dashboard_command_center_v3.html")
        print(f"[NAVEGO DASHBOARD] Endpoint /captura: http://localhost:{PORT}/captura")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[NAVEGO DASHBOARD] Detención solicitada.")
            httpd.server_close()
