#!/usr/bin/env python3
"""
Verificacion empirica de H-2026-0014 a H-2026-0018.

Fuente unica: docs/gnss/gnss_simulado.jsonl (62 fixes).
Config de referencia: docs/gnss/03_scenario.json (solo lectura).

Este script NO modifica datos. Solo lee y reporta.
Uso:  python3 tools/gnss/verify_h0014_0018.py
"""
import json
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "docs" / "gnss" / "gnss_simulado.jsonl"
CFG = ROOT / "docs" / "gnss" / "03_scenario.json"

R_EARTH = 6371000.0  # radio medio terrestre, metros


def load_fixes(path):
    fixes = []
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                fixes.append(json.loads(line))
            except json.JSONDecodeError as exc:
                sys.exit(f"ERROR: linea {lineno} no es JSON valido: {exc}")
    return fixes


def haversine(lat1, lon1, lat2, lon2):
    """Distancia en metros entre dos puntos GPS."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R_EARTH * math.asin(math.sqrt(a))


def project_local(lat, lon, lat0, lon0):
    """Proyeccion equirectangular local a metros (x=este, y=norte)."""
    x = math.radians(lon - lon0) * R_EARTH * math.cos(math.radians(lat0))
    y = math.radians(lat - lat0) * R_EARTH
    return x, y


def perp_distance(px, py, ax, ay, bx, by):
    """Distancia perpendicular del punto P a la recta AB (infinita)."""
    dx, dy = bx - ax, by - ay
    norm = math.hypot(dx, dy)
    if norm == 0:
        return math.hypot(px - ax, py - ay)
    return abs(dy * px - dx * py + bx * ay - by * ax) / norm


def main():
    if not LOG.exists():
        sys.exit(f"ERROR: no existe {LOG}")
    fixes = load_fixes(LOG)
    n = len(fixes)
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    gnss = cfg["gnss"]
    sigma = gnss["noise_sigma_m"]
    latency_cfg = gnss["latency_ms"]
    spike_p = gnss["spikes"]["probability"]
    spike_min = gnss["spikes"]["min_jump_m"]

    print("=" * 72)
    print("VERIFICACION H-2026-0014 .. H-2026-0018")
    print(f"Fuente: {LOG.relative_to(ROOT)}")
    print(f"Fixes cargados: {n}")
    print("=" * 72)

    results = {}

    # ---------- H-2026-0014 : accuracy constante = 4.5 ----------
    print("\n### H-2026-0014 — accuracy constante en 4.5")
    accs = [f["accuracy"] for f in fixes]
    uniq = sorted(set(accs))
    n_ok = sum(1 for a in accs if a == 4.5)
    print(f"  Valores unicos de accuracy : {uniq}")
    print(f"  Fixes con accuracy == 4.5  : {n_ok}/{n}")
    print(f"  Config sigma_m             : {sigma} (sigma*1.5 = {sigma * 1.5})")
    if uniq == [4.5]:
        results["H-2026-0014"] = ("CONFIRMADA",
            f"los {n} fixes tienen accuracy = 4.5 exactamente; "
            f"coincide con sigma_m*1.5 = {sigma * 1.5}")
    else:
        results["H-2026-0014"] = ("REFUTADA",
            f"hay {len(uniq)} valores distintos de accuracy: {uniq}")
    print(f"  => {results['H-2026-0014'][0]}: {results['H-2026-0014'][1]}")

    # ---------- H-2026-0016 : latencia = 300 ms ----------
    print("\n### H-2026-0016 — latencia pura receivedAt - measuredAt = 300 ms")
    lats = [f["receivedAt"] - f["measuredAt"] for f in fixes]
    lat_uniq = sorted(set(lats))
    print(f"  Valores unicos de latencia : {lat_uniq}")
    print(f"  Config latency_ms          : {latency_cfg}")
    if lat_uniq == [latency_cfg]:
        results["H-2026-0016"] = ("CONFIRMADA",
            f"los {n} fixes tienen receivedAt - measuredAt = {latency_cfg} ms exactos")
    else:
        bad = [(i + 1, v) for i, v in enumerate(lats) if v != latency_cfg]
        results["H-2026-0016"] = ("REFUTADA",
            f"latencia no uniforme; {len(bad)} fixes difieren de {latency_cfg}: {bad[:5]}")
    print(f"  => {results['H-2026-0016'][0]}: {results['H-2026-0016'][1]}")

    # ---------- H-2026-0018 : 0 o 1 spike > 50 m ----------
    print("\n### H-2026-0018 — 0 o 1 spike > 50 m entre fixes consecutivos")
    segs = []
    for i in range(1, n):
        a, b = fixes[i - 1], fixes[i]
        d = haversine(a["latitude"], a["longitude"], b["latitude"], b["longitude"])
        segs.append((i + 1, d))  # numero de fix destino (1-based)
    spikes = [(idx, d) for idx, d in segs if d > spike_min]
    med = statistics.median([d for _, d in segs])
    print(f"  Config spike.probability   : {spike_p}")
    print(f"  Esperado en {n} fixes        : {n * spike_p:.2f} spikes")
    print(f"  Mediana de salto           : {med:.2f} m")
    print(f"  Spikes > {spike_min} m           : {len(spikes)}")
    for idx, d in spikes:
        print(f"     fix #{idx}: salto {d:.2f} m")
    if len(spikes) <= 1:
        results["H-2026-0018"] = ("CONFIRMADA",
            f"{len(spikes)} spike(s) > {spike_min} m en {n} fixes (esperado {n * spike_p:.2f})")
    else:
        results["H-2026-0018"] = ("REFUTADA",
            f"{len(spikes)} spikes > {spike_min} m: "
            + ", ".join(f"fix#{i}={d:.1f}m" for i, d in spikes))
    print(f"  => {results['H-2026-0018'][0]}: {results['H-2026-0018'][1]}")

    # ---------- H-2026-0017 : distancia perpendicular ~ sigma ----------
    print("\n### H-2026-0017 — distancia perpendicular media ~ sigma = 3.0 m")
    lat0, lon0 = fixes[0]["latitude"], fixes[0]["longitude"]
    pts = [project_local(f["latitude"], f["longitude"], lat0, lon0) for f in fixes]
    ax, ay = pts[0]
    bx, by = pts[-1]
    dists = [perp_distance(px, py, ax, ay, bx, by) for px, py in pts]
    mean_d = statistics.mean(dists)
    sd_d = statistics.pstdev(dists)
    print(f"  Recta de referencia        : fix#1 -> fix#{n}")
    print(f"  Distancia perpendicular    : media {mean_d:.3f} m, sd {sd_d:.3f} m")
    print(f"  Min / Max                  : {min(dists):.3f} / {max(dists):.3f} m")
    print(f"  Sigma configurado          : {sigma} m")
    print(f"  Rango de falsacion         : [2.0, 4.5] m")
    if 2.0 <= mean_d <= 4.5:
        results["H-2026-0017"] = ("CONFIRMADA",
            f"media perpendicular {mean_d:.3f} m dentro de [2.0, 4.5] m (sigma={sigma})")
    else:
        results["H-2026-0017"] = ("REFUTADA",
            f"media perpendicular {mean_d:.3f} m fuera de [2.0, 4.5] m (sigma={sigma})")
    print(f"  => {results['H-2026-0017'][0]}: {results['H-2026-0017'][1]}")

    # ---------- H-2026-0015 : heading congelado post-corte ----------
    print("\n### H-2026-0015 — heading congelado post-corte (fix 31..62)")
    cut = gnss["cut_windows"][0]
    cut_start_ms = fixes[0]["measuredAt"] + cut["start_s"] * 1000
    post = [(i + 1, f) for i, f in enumerate(fixes) if f["measuredAt"] >= cut_start_ms]
    pre = [(i + 1, f) for i, f in enumerate(fixes) if f["measuredAt"] < cut_start_ms]
    print(f"  Corte configurado          : inicio {cut['start_s']}s, duracion {cut['duration_s']}s")
    print(f"  Fixes pre-corte            : {len(pre)} (ultimo #{pre[-1][0]})")
    print(f"  Fixes post-corte           : {len(post)} (primero #{post[0][0]})")
    pre_h = sorted(set(f["heading"] for _, f in pre))
    post_h = sorted(set(f["heading"] for _, f in post))
    print(f"  Headings unicos pre-corte  : {len(pre_h)} -> {pre_h[:6]}{' ...' if len(pre_h) > 6 else ''}")
    print(f"  Headings unicos post-corte : {len(post_h)} -> {post_h}")
    frozen = len(post_h) == 1
    if frozen:
        val = post_h[0]
        results["H-2026-0015"] = ("CONFIRMADA",
            f"los {len(post)} fixes post-corte tienen heading identico = {val} "
            f"(1 valor unico); el simulador no inyecta jitter post-recuperacion")
    else:
        results["H-2026-0015"] = ("REFUTADA",
            f"el heading varia post-corte: {len(post_h)} valores unicos")
    print(f"  => {results['H-2026-0015'][0]}: {results['H-2026-0015'][1]}")

    # ---------- Resumen ----------
    print("\n" + "=" * 72)
    print("RESUMEN")
    print("=" * 72)
    tally = {}
    for hid in ["H-2026-0014", "H-2026-0015", "H-2026-0016",
                "H-2026-0017", "H-2026-0018"]:
        verdict, detail = results[hid]
        tally[verdict] = tally.get(verdict, 0) + 1
        print(f"  {hid}  {verdict:<11} {detail}")
    print("-" * 72)
    print("  " + ", ".join(f"{k}: {v}" for k, v in sorted(tally.items())))
    print("=" * 72)
    return results


if __name__ == "__main__":
    main()
