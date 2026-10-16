#!/usr/bin/env python3
"""E2b - Sensibilidad del giro al torque de timon.
Solo lectura sobre simulador_polaris y timonel.
Escribe resultados a e2b_sensibilidad.json y stdout."""

import sys, math, json, statistics
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import simulador_polaris as sim
from simulador_polaris import Barco, DT

TORQUES = [886.0, 1500.0, 2500.0, 4000.0, 5500.0]
REPETICIONES = 3
DURACION_S = 30.0
COMANDO_PERIOD_S = 3.0
TIMON_MS = 1500

def correr_una(torque_val):
    # override
    sim.TIMON_TORQUE = torque_val
    b = Barco()
    t = 0.0
    next_cmd = 0.0
    hdg_inicial = b.heading_deg()
    hdg_hist = []
    yaw_rate_hist = []
    dist_recorrida = 0.0
    while t < DURACION_S:
        b.paso()
        t += DT
        dist_recorrida += math.hypot(b.vel_x, b.vel_z) * DT
        if t >= next_cmd:
            b.aplicar_comando(timon=1, timon_ms=TIMON_MS, avance=1, avance_ms=1500)
            next_cmd = t + COMANDO_PERIOD_S
        hdg_hist.append(b.heading_deg())
        yaw_rate_hist.append(b.yaw_rate)
    delta_hdg = (b.heading_deg() - hdg_inicial + 360) % 360
    if delta_hdg > 180: delta_hdg -= 360
    # primeras 3 s para alpha inicial
    n0 = int(3.0 / DT)
    alpha_inicial = (yaw_rate_hist[n0] - yaw_rate_hist[0]) / 3.0
    omega_media = statistics.mean(abs(y) for y in yaw_rate_hist[n0:])
    return {
        "torque_nm": torque_val,
        "delta_hdg_deg": round(delta_hdg, 3),
        "alpha_inicial_rad_s2": round(alpha_inicial, 6),
        "omega_media_deg_s": round(math.degrees(omega_media), 3),
        "dist_recorrida_m": round(dist_recorrida, 3),
        "pos_final_x": round(b.pos_x, 3),
        "pos_final_z": round(b.pos_z, 3),
    }

def main():
    resultados = []
    for torq in TORQUES:
        print(f"Corriendo TORQUE={torq}...")
        for r in range(REPETICIONES):
            res = correr_una(torq)
            resultados.append(res)
            print(f"  rep {r+1}: Δhdg={res['delta_hdg_deg']:+7.2f}° ω_med={res['omega_media_deg_s']:.3f}°/s")
    Path("e2b_sensibilidad.json").write_text(json.dumps(resultados, indent=2))
    print()
    print("=== RESUMEN ===")
    print(f"{'TORQUE':>8} | {'Δhdg_med':>10} | {'ω_med':>10} | {'α_inicial':>12}")
    print("-" * 50)
    for torq in TORQUES:
        rs = [r for r in resultados if r["torque_nm"] == torq]
        dh = statistics.mean([r["delta_hdg_deg"] for r in rs])
        wm = statistics.mean([r["omega_media_deg_s"] for r in rs])
        ai = statistics.mean([r["alpha_inicial_rad_s2"] for r in rs])
        print(f"{torq:>8.0f} | {dh:>10.2f} | {wm:>10.3f} | {ai:>12.5f}")

if __name__ == "__main__":
    main()
