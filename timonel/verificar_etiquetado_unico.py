#!/usr/bin/env python3
"""verificar_etiquetado_unico.py - Prueba de identidad (F0 bloqueante 1).

Verifica que los bancos existentes (A2, probe, 0b) se regeneran
identicos usando la funcion unica de etiquetado.

Correr: cd timonel && python3 verificar_etiquetado_unico.py
"""
import json
import sys

from etiquetar import etiquetar_por_T, etiquetar_por_T_v


def verificar_banco(path, modo):
    """modo: 'T' (solo distancia) o 'T_v' (distancia + velocidad)."""
    with open(path, encoding="utf-8") as f:
        contextos = [json.loads(l) for l in f]

    total = 0
    fallos = []
    for i, c in enumerate(contextos):
        total += 1
        d = c.get("d")
        T = c.get("T")
        label_real = c.get("label")
        if modo == "T":
            label_calc = etiquetar_por_T(d, T)
        elif modo == "T_v":
            v = c.get("v")
            v_max = c.get("v_max")
            if v_max is None:
                # B1 placebo en 0b: sin clausula de velocidad
                label_calc = etiquetar_por_T(d, T)
            else:
                label_calc = etiquetar_por_T_v(d, T, v, v_max)
        else:
            raise ValueError("modo desconocido: " + modo)

        if label_calc != label_real:
            fallos.append((i, d, T, c.get("v"), c.get("v_max"),
                           label_real, label_calc))

    return total, fallos


def main():
    bancos = [
        ("bancoA2/train.jsonl", "T"),
        ("bancoA2/val.jsonl", "T"),
        ("bancoA2/test_interp.jsonl", "T"),
        ("bancoA2/test_extrap.jsonl", "T"),
        ("bancoA2_probe/probe.jsonl", "T_v"),
        ("bancoA2_0b/probe_0b.jsonl", "T_v"),
    ]

    fallos_totales = 0
    for path, modo in bancos:
        try:
            total, fallos = verificar_banco(path, modo)
        except FileNotFoundError:
            print("SKIP: " + path + " (no existe)")
            continue

        if not fallos:
            print("OK: " + path + " (" + str(total) + " contextos, 0 fallos)")
        else:
            print("FALLA: " + path + " (" + str(len(fallos)) + " fallos de "
                  + str(total) + ")")
            for f in fallos[:5]:
                print("  idx=" + str(f[0]) + " d=" + str(f[1]) + " T=" + str(f[2])
                      + " v=" + str(f[3]) + " vmax=" + str(f[4])
                      + " real=" + str(f[5]) + " calc=" + str(f[6]))
            fallos_totales += len(fallos)

    print()
    if fallos_totales == 0:
        print("TODOS LOS BANCOS REGENERAN IDENTICOS")
        return 0
    print(str(fallos_totales) + " FALLOS TOTALES")
    return 1


if __name__ == "__main__":
    sys.exit(main())
