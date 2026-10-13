#!/usr/bin/env python3
"""baseline_pstruct.py - P-struct: motor deterministico.

Recibe (T, v_max, d, v) estructurados y devuelve la accion correcta.
Es la cota superior de A3: mide lo que se puede lograr cuando la
spec esta perfectamente parseada.

Usa etiquetar_por_T_v como motor. Espera 100% en todos los bancos.

Uso:
  python3 baseline_pstruct.py                    (todos los bancos)
  python3 baseline_pstruct.py bancoA3/train.jsonl
"""
import json
import sys
from pathlib import Path

from etiquetar import etiquetar_por_T, etiquetar_por_T_v


def predecir(ctx):
    """Aplica la regla a un contexto estructurado."""
    if ctx.get("v_max") is None or ctx.get("v") is None:
        return etiquetar_por_T(ctx["d"], ctx["T"])
    return etiquetar_por_T_v(ctx["d"], ctx["T"], ctx["v"], ctx["v_max"])


def evaluar(path):
    with open(path, encoding="utf-8") as f:
        ctxs = [json.loads(l) for l in f]
    aciertos = 0
    fallos = []
    for i, c in enumerate(ctxs):
        pred = predecir(c)
        if pred == c["label"]:
            aciertos += 1
        else:
            fallos.append((i, c, pred))
    return len(ctxs), aciertos, fallos


def main():
    if len(sys.argv) > 1:
        paths = sys.argv[1:]
    else:
        base = Path("bancoA3")
        paths = [
            str(base / "train.jsonl"),
            str(base / "val.jsonl"),
            str(base / "test_interp.jsonl"),
            str(base / "test_extrap.jsonl"),
            str(base / "test_balanceado.jsonl"),
        ]

    total_global = 0
    aciertos_global = 0
    for p in paths:
        try:
            n, k, fallos = evaluar(p)
        except FileNotFoundError:
            print("SKIP: " + p + " (no existe)")
            continue
        acc = k / n if n else 0
        print(f"  {p}: {k}/{n} = {acc:.4f}")
        if fallos:
            for f in fallos[:3]:
                print(f"    idx={f[0]} real={f[1]['label']} pred={f[2]}")
        total_global += n
        aciertos_global += k

    print()
    if total_global:
        print(f"GLOBAL P-struct: {aciertos_global}/{total_global} = "
              f"{aciertos_global/total_global:.4f}")
    if aciertos_global == total_global:
        print("P-STRUCT: 100% (cota superior, comportamiento esperado)")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
