#!/usr/bin/env python3
"""
Refinamiento de H-2026-0017 y H-2026-0018.

Motivo: los fixes #25 y #26 muestran saltos consecutivos de ~179 m y ~178 m.
Eso puede ser UN spike que vuelve (outlier de 1 fix) contado dos veces,
o DOS spikes independientes. Hay que distinguirlo.

Ademas H-2026-0017 se calculo con la recta fix#1->fix#62, que pasa cerca
del outlier y contamina media y sd. Se recalcula con metodos robustos.

Solo lee. No modifica datos.
"""
import json
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "docs" / "gnss" / "gnss_simulado.jsonl"
R_EARTH = 6371000.0


def load_fixes(path):
    with path.open(encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def haversine(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R_EARTH * math.asin(math.sqrt(a))


def project_local(lat, lon, lat0, lon0):
    return (math.radians(lon - lon0) * R_EARTH * math.cos(math.radians(lat0)),
            math.radians(lat - lat0) * R_EARTH)


def perp_distance(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    norm = math.hypot(dx, dy)
    if norm == 0:
        return math.hypot(px - ax, py - ay)
    return abs(dy * px - dx * py + bx * ay - by * ax) / norm


def fit_line(pts):
    """Ajuste por minimos cuadrados y = m*x + b."""
    n = len(pts)
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    num = sum((p[0] - mx) * (p[1] - my) for p in pts)
    den = sum((p[0] - mx) ** 2 for p in pts)
    m = num / den if den else 0.0
    return m, my - m * mx


def main():
    fixes = load_fixes(LOG)
    n = len(fixes)

    print("=" * 74)
    print("REFINAMIENTO — H-2026-0017 (sigma) y H-2026-0018 (spikes)")
    print("=" * 74)

    # ================= H-2026-0018 : uno o dos spikes? =================
    print("\n### H-2026-0018 — ¿1 spike que vuelve, o 2 spikes?")
    segs = []
    for i in range(1, n):
        a, b = fixes[i - 1], fixes[i]
        segs.append((i + 1, haversine(a["latitude"], a["longitude"],
                                      b["latitude"], b["longitude"])))
    big = [(idx, d) for idx, d in segs if d > 50]
    print(f"  Saltos > 50 m: {[(i, round(d,1)) for i, d in big]}")

    # Si un fix es outlier, el salto de ENTRADA y el de SALIDA son ambos grandes.
    # Si son spikes independientes, hay fixes "normales" entre medio.
    for idx, d in big:
        prev_f = fixes[idx - 2]
        cur_f = fixes[idx - 1]
        print(f"\n  fix #{idx}: salto {d:.1f} m desde fix #{idx-1}")
        print(f"    fix #{idx-1} lat/lon: {prev_f['latitude']:.6f}, {prev_f['longitude']:.6f}")
        print(f"    fix #{idx}   lat/lon: {cur_f['latitude']:.6f}, {cur_f['longitude']:.6f}")

    # Prueba decisiva: comparar distancia fix#24 -> fix#27.
    # Si el fix#25 y #26 son ambos outliers aislados, la trayectoria
    # "sana" #24->#27 es corta.
    d_24_25 = next(d for i, d in segs if i == 25)
    d_25_26 = next(d for i, d in segs if i == 26)
    d_26_27 = next(d for i, d in segs if i == 27)
    d_24_27 = haversine(fixes[23]["latitude"], fixes[23]["longitude"],
                        fixes[26]["latitude"], fixes[26]["longitude"])
    print(f"\n  Cadena de saltos alrededor del evento:")
    print(f"    #24->#25 : {d_24_25:8.2f} m")
    print(f"    #25->#26 : {d_25_26:8.2f} m")
    print(f"    #26->#27 : {d_26_27:8.2f} m")
    print(f"    #24->#27 (directo, salteando #25 y #26): {d_24_27:8.2f} m")

    if d_25_26 > 50 and d_24_27 < 50:
        verdict18 = "CONFIRMADA"
        detail18 = (f"1 evento de spike, no 2. El fix #25 sale de la trayectoria "
                    f"(salto {d_24_25:.1f} m) y el #26 vuelve (salto {d_26_27:.1f} m); "
                    f"la distancia #24->#27 es solo {d_24_27:.1f} m. El salto #25->#26 "
                    f"({d_25_26:.1f} m) es el mismo outlier cruzando de ida y vuelta, "
                    f"por eso el conteo bruto de saltos >50 m da 2. Spikes reales = 1.")
    else:
        verdict18 = "REFUTADA"
        detail18 = f"2 o mas eventos de spike independientes (cadena #24->#27 = {d_24_27:.1f} m)"
    print(f"  => {verdict18}: {detail18}")

    # ================= H-2026-0017 : sigma sin contaminacion =================
    print("\n### H-2026-0017 — distancia perpendicular a la recta (robusta)")
    lat0, lon0 = fixes[0]["latitude"], fixes[0]["longitude"]
    pts = [project_local(f["latitude"], f["longitude"], lat0, lon0) for f in fixes]

    # Metodo A: recta fix#1 -> fix#62 (el del criterio original)
    ax, ay = pts[0]
    bx, by = pts[-1]
    dA = [perp_distance(px, py, ax, ay, bx, by) for px, py in pts]
    print(f"\n  [A] Recta fix#1 -> fix#62 (metodo original del criterio)")
    print(f"      media {statistics.mean(dA):.3f} m | sd {statistics.pstdev(dA):.3f} m | max {max(dA):.3f} m")

    # Metodo B: excluyendo los fixes del evento de spike (#25, #26)
    keep = [p for i, p in enumerate(pts) if (i + 1) not in (25, 26)]
    ax2, ay2 = keep[0]
    bx2, by2 = keep[-1]
    dB = [perp_distance(px, py, ax2, ay2, bx2, by2) for px, py in keep]
    print(f"  [B] Excluyendo #25 y #26 (n={len(keep)})")
    print(f"      media {statistics.mean(dB):.3f} m | sd {statistics.pstdev(dB):.3f} m | max {max(dB):.3f} m")

    # Metodo C: recta ajustada por minimos cuadrados sobre datos limpios
    m, b = fit_line(keep)
    dC = [abs(m * px - py + b) / math.hypot(m, 1.0) for px, py in keep]
    print(f"  [C] Ajuste minimos cuadrados (datos limpios)")
    print(f"      pendiente {m:.5f} | media {statistics.mean(dC):.3f} m | sd {statistics.pstdev(dC):.3f} m")

    # Metodo D: mediana (robusta a outliers, sin excluir nada)
    medD = statistics.median(dA)
    print(f"  [D] Mediana sobre todos los fixes (robusta): {medD:.3f} m")

    print(f"\n  Criterio de falsacion original: media en [2.0, 4.5] m")
    mean_clean = statistics.mean(dC)
    if 2.0 <= mean_clean <= 4.5:
        verdict17 = "CONFIRMADA"
        detail17 = (f"con el outlier excluido, la distancia perpendicular media es "
                    f"{mean_clean:.3f} m (dentro de [2.0, 4.5], consistente con sigma=3.0). "
                    f"El valor {statistics.mean(dA):.3f} m del calculo crudo estaba "
                    f"contaminado por el spike del fix #25.")
    else:
        verdict17 = "REFUTADA"
        detail17 = f"media limpia {mean_clean:.3f} m fuera de [2.0, 4.5] m"
    print(f"  => {verdict17}: {detail17}")

    print("\n" + "=" * 74)
    print("CONCLUSION REFINADA")
    print("=" * 74)
    print(f"  H-2026-0017  {verdict17}")
    print(f"  H-2026-0018  {verdict18}")
    print("=" * 74)
    return verdict17, verdict18


if __name__ == "__main__":
    main()
