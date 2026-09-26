#!/usr/bin/env python3
"""
H2/H3: evalua la regla "dt > umbral O speed ~ 0" sobre el dataset
generado por run_ruido_vs_gap.py y mide la separacion N+1.

No regenera fixes: lee resultados_ruido_vs_gap.json y los fixes
crudos ya escritos en disco.
"""
import json
import math
import os

BASE = os.path.dirname(os.path.abspath(__file__))
MAX_JUMP = 15.0
DT_UMBRAL_S = 2.0
SPEED_ZERO_MS = 0.3
SIGMAS = [0.5, 1.5, 3.0, 5.0]
SEEDS = [7100, 7101, 7102, 7103, 7104]


def hav(a, b):
    R = 6371000.0
    la1, lo1 = math.radians(a["latitude"]), math.radians(a["longitude"])
    la2, lo2 = math.radians(b["latitude"]), math.radians(b["longitude"])
    h = (math.sin((la2 - la1) / 2) ** 2
         + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(h))


def load(p):
    with open(p) as f:
        return [json.loads(l) for l in f if l.strip()]


def classify(fixes):
    """Aplica la regla a cada salto >15 m. Devuelve TP/FP/FN."""
    tp = fp = fn = 0
    falsos_pos = []
    falsos_neg = []
    for i in range(1, len(fixes)):
        a, b = fixes[i - 1], fixes[i]
        d = hav(a, b)
        if d <= MAX_JUMP:
            continue
        dt = (b["receivedAt"] - a["receivedAt"]) / 1000.0
        sp = b.get("speed", 0.0)
        regla_dice_gap = (dt > DT_UMBRAL_S) or (sp <= SPEED_ZERO_MS)
        # Ground truth: en el set de ruido NO hay gaps programados,
        # luego todo salto es ruido (FP si la regla dice gap). En el
        # set de gap real, el unico salto legitimo es el del corte.
        return regla_dice_gap, dt, d, sp
    return None


def main():
    # --- Ruido: todo salto >15 m es un falso gap del tracker ---
    print("=== H2: regla dt>%.0fs O speed<=%.1f m/s sobre RUIDO ==="
          % (DT_UMBRAL_S, SPEED_ZERO_MS))
    tot_ruido = tot_clasif_gap = 0
    for sigma in SIGMAS:
        crudos = 0
        clasif_gap = 0
        dts = []
        for seed in SEEDS:
            path = os.path.join(BASE, f"fixes_ruido_sigma{sigma}_S{seed}.jsonl")
            if not os.path.exists(path):
                continue
            fixes = load(path)
            sigma_jumps = 0
            for i in range(1, len(fixes)):
                a, b = fixes[i - 1], fixes[i]
                d = hav(a, b)
                if d <= MAX_JUMP:
                    continue
                dt = (b["receivedAt"] - a["receivedAt"]) / 1000.0
                sp = b.get("speed", 0.0)
                sigma_jumps += 1
                dts.append((round(dt, 2), round(sp, 2), round(d, 1)))
                if dt > DT_UMBRAL_S or sp <= SPEED_ZERO_MS:
                    clasif_gap += 1
            crudos += sigma_jumps
        tot_ruido += crudos
        tot_clasif_gap += clasif_gap
        print(f"sigma={sigma:>4} m: saltos>15m={crudos:>4}  "
              f"clasificados gap por la regla={clasif_gap}  "
              f"({100.0*clasif_gap/crudos if crudos else 0:.1f}%)")
        if crudos and sigma >= 3.0:
            print(f"           dt/speed/|salto| muestra: {dts[:6]}")
    print(f"TOTAL ruido: saltos={tot_ruido} -> FP regla={tot_clasif_gap} "
          f"({100.0*tot_clasif_gap/tot_ruido if tot_ruido else 0:.1f}%)")

    # --- Gap real: el salto legitimo debe clasificarse gap ---
    print("\n=== H2 sobre GAP REAL (10 s) ===")
    tp = fn = 0
    backs_gap = []
    backs_ruido = []
    for seed in [7100, 7101, 7102]:
        p = os.path.join(BASE, f"fixes_gapreal10s_S{seed}.jsonl")
        if not os.path.exists(p):
            continue
        fixes = load(p)
        for i in range(1, len(fixes)):
            a, b = fixes[i - 1], fixes[i]
            d = hav(a, b)
            if d <= MAX_JUMP:
                continue
            dt = (b["receivedAt"] - a["receivedAt"]) / 1000.0
            sp = b.get("speed", 0.0)
            ok = dt > DT_UMBRAL_S or sp <= SPEED_ZERO_MS
            tp += 1 if ok else 0
            fn += 0 if ok else 1
            if i + 1 < len(fixes):
                backs_gap.append(round(hav(a, fixes[i + 1]), 1))
            print(f"seed={seed}: dt={dt:.1f}s speed={sp:.2f} m/s "
                  f"salto={d:.1f}m -> regla dice gap={ok}")
    print(f"GAP REAL: detectados={tp} no detectados={fn} "
          f"({100.0*tp/(tp+fn) if tp+fn else 0:.1f}% recall)")

    # --- H3: N+1 vuelve al punto pre-salto? ---
    print("\n=== H3: |fix N+1 - fix N-1| tras un salto >15 m ===")
    for sigma in [3.0, 5.0]:
        backs = []
        for seed in SEEDS:
            p = os.path.join(BASE, f"fixes_ruido_sigma{sigma}_S{seed}.jsonl")
            if not os.path.exists(p):
                continue
            fx = load(p)
            for i in range(1, len(fx) - 1):
                a, b = fx[i - 1], fx[i]
                if hav(a, b) <= MAX_JUMP:
                    continue
                backs.append(round(hav(a, fx[i + 1]), 1))
        if backs:
            backs.sort()
            print(f"RUIDO sigma={sigma}: n={len(backs)} "
                  f"mediana={backs[len(backs)//2]}m "
                  f"<5m={sum(1 for x in backs if x < 5)}/{len(backs)} "
                  f"(={100.0*sum(1 for x in backs if x < 5)/len(backs):.0f}%) "
                  f">20m={sum(1 for x in backs if x > 20)}")
    if backs_gap:
        backs_gap.sort()
        print(f"GAP REAL: n={len(backs_gap)} valores={backs_gap} "
              f">20m={sum(1 for x in backs_gap if x > 20)}/{len(backs_gap)}")


if __name__ == "__main__":
    main()
