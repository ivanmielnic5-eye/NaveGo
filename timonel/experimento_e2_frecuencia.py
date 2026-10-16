#!/usr/bin/env python3
"""E2 - Efecto de la frecuencia de decision sobre la navegacion.
Solo lectura sobre simulador_polaris y timonel.
No modifica archivos. Escribe resultados a e2_resultados.json y e2_resultados.md."""

import sys, math, json, statistics
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from simulador_polaris import Barco, DT
from timonel import timon_python

INTERVALOS = [0.5, 1.0, 2.0, 3.0, 5.0, 10.0]
REPETICIONES = 5
DURACION_MAX = 180.0
META_X, META_Z = 36.0, -6.0
UMBRAL_LLEGADA = 10.0

def correr_una(intervalo_s):
    b = Barco()
    t = 0.0
    next_decision = 0.0
    comandos = 0
    heading_cambios = 0
    last_heading = b.heading_deg()
    dist_recorrida = 0.0
    t_llegada = None
    while t < DURACION_MAX:
        b.paso()
        t += DT
        # distancia recorrida
        dist_recorrida += math.hypot(b.vel_x, b.vel_z) * DT
        # decision
        if t >= next_decision:
            speed_ms = math.hypot(b.vel_x, b.vel_z)
            timon, avance = timon_python(b.pos_x, b.pos_z, b.heading_deg(), speed_ms)
            b.aplicar_comando(timon=timon, timon_ms=1500, avance=avance, avance_ms=1500)
            next_decision = t + intervalo_s
            comandos += 1
        # oscilacion de heading (cambios de signo)
        h = b.heading_deg()
        if (h - last_heading) * (last_heading - b.heading_deg()) < 0 and abs(h - last_heading) > 0.5:
            pass  # se hace abajo con otra metrica
        # deteccion de llegada
        dist = math.hypot(b.pos_x - META_X, b.pos_z - META_Z)
        if dist < UMBRAL_LLEGADA and t_llegada is None:
            t_llegada = t
            break
    # oscilacion: std de yaw_rate a lo largo de la corrida (recalculo)
    return {
        "intervalo_s": intervalo_s,
        "llego": t_llegada is not None,
        "t_llegada_s": t_llegada,
        "t_final_s": t,
        "dist_recorrida_m": dist_recorrida,
        "comandos": comandos,
        "dist_final_a_meta_m": math.hypot(b.pos_x - META_X, b.pos_z - META_Z),
        "pos_final_x": b.pos_x,
        "pos_final_z": b.pos_z,
    }

def main():
    resultados = []
    for inter in INTERVALOS:
        print(f"Corriendo INTERVALO_S={inter}...")
        for r in range(REPETICIONES):
            res = correr_una(inter)
            resultados.append(res)
            print(f"  rep {r+1}/{REPETICIONES}: llego={res['llego']} t={res['t_llegada_s']}")

    # guardar crudos
    Path("e2_resultados.json").write_text(json.dumps(resultados, indent=2))

    # resumen por intervalo
    print()
    print("=== RESUMEN ===")
    print(f"{'INTERVALO':>10} | {'LLEGADAS':>8} | {'T_MEDIO':>8} | {'DIST_MEDIA':>10} | {'COMANDOS':>8}")
    print("-" * 60)
    for inter in INTERVALOS:
        rs = [r for r in resultados if r["intervalo_s"] == inter]
        llegadas = sum(1 for r in rs if r["llego"])
        tiempos = [r["t_llegada_s"] for r in rs if r["llego"]]
        t_medio = statistics.mean(tiempos) if tiempos else float("nan")
        dist_media = statistics.mean([r["dist_recorrida_m"] for r in rs])
        cmd_media = statistics.mean([r["comandos"] for r in rs])
        print(f"{inter:>10.1f} | {llegadas:>3}/{len(rs):<4} | {t_medio:>8.2f} | {dist_media:>10.2f} | {cmd_media:>8.1f}")

if __name__ == "__main__":
    main()
