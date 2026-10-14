#!/usr/bin/env python3
"""validar_fheld.py - Valida la generacion bruta de F-held.

Chequea:
- Cuenta de formulaciones (esperado 60, tolerancia +/- 5).
- Presencia de {vmax} y "nudos" en cada linea.
- Ausencia de las 4 construcciones prohibidas.
- Sin numeracion ni bullets.
"""
import re
import sys
from pathlib import Path

PROHIBIDAS = [
    re.compile(r"menor o igual a\s+\{vmax\}\s+nudos", re.I),
    re.compile(r"no supere los\s+\{vmax\}\s+nudos", re.I),
    re.compile(r"no este navegando a mas de\s+\{vmax\}\s+nudos", re.I),
    re.compile(r"sea como maximo\s+\{vmax\}\s+nudos", re.I),
]

def main():
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "fheld_generado_bruto.txt")
    with open(path, encoding="utf-8") as f:
        lineas = [l.rstrip("\n") for l in f if l.strip()]

    errores = []
    print(f"Lineas: {len(lineas)}")

    if not (55 <= len(lineas) <= 65):
        errores.append(f"cuenta fuera de rango: {len(lineas)}")

    sin_vmax = 0
    sin_nudos = 0
    con_numero = 0
    con_bullet = 0
    con_prohibida = 0
    for i, ln in enumerate(lineas, 1):
        if "{vmax}" not in ln:
            sin_vmax += 1
        if "nudos" not in ln.lower():
            sin_nudos += 1
        if re.match(r"^\s*\d+[\.\)]", ln):
            con_numero += 1
        if re.match(r"^\s*[-*•]", ln):
            con_bullet += 1
        for rex in PROHIBIDAS:
            if rex.search(ln):
                con_prohibida += 1
                errores.append(f"linea {i}: construccion prohibida -> {ln[:60]}")
                break

    print(f"Sin {{vmax}}: {sin_vmax}")
    print(f"Sin 'nudos': {sin_nudos}")
    print(f"Con numeracion: {con_numero}")
    print(f"Con bullet: {con_bullet}")
    print(f"Con prohibida exacta: {con_prohibida}")

    if sin_vmax: errores.append(f"{sin_vmax} lineas sin {{vmax}}")
    if sin_nudos: errores.append(f"{sin_nudos} lineas sin 'nudos'")
    if con_numero: errores.append(f"{con_numero} lineas con numeracion")
    if con_bullet: errores.append(f"{con_bullet} lineas con bullet")

    print()
    if errores:
        print("ERRORES:")
        for e in errores:
            print(f"  {e}")
        return 1
    print("VALIDACION OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
