#!/usr/bin/env python3
"""guardian_f0.py - Test guardian de F0.

Busca literales 15.0 prohibidos en archivos migrados de F0.
Falla si encuentra alguno no esperado.

Referencia: borradores/luna_alcance_f0.md.
"""
import re
import sys

# Archivos migrados de F0 (deben estar limpios)
MIGRADOS = [
    "generar_banco_A2.py",
    "etiquetar.py",
    "criterios_mision.py",
]

# Patron: 15, 15.0, 15.00 (pero no 150, 1500)
PATRON = re.compile(r"(?<![\d.])15(\.0+)?(?![\d])")

# Excepciones documentadas: (archivo, linea, razon)
EXCEPCIONES = [
    # (archivo, linea, razon)
    ("generar_banco_A2.py", 226, "etiqueta del baseline, no umbral de mision"),
    ("generar_banco_A2.py", 229, "calculo del baseline T=15 fijo, no umbral de mision"),
]


def revisar_archivo(path):
    """Devuelve lista de (linea, texto) con literales encontrados."""
    encontrados = []
    with open(path, encoding="utf-8") as f:
        for i, ln in enumerate(f, 1):
            # Ignorar lineas de comentario simples
            s = ln.rstrip("\n")
            for m in PATRON.finditer(s):
                # Ver si esta en excepciones
                es_excepcion = any(
                    e[0] == path and e[1] == i for e in EXCEPCIONES
                )
                if not es_excepcion:
                    encontrados.append((i, s.strip()))
                    break
    return encontrados


def main():
    fallos = 0
    for archivo in MIGRADOS:
        try:
            encontrados = revisar_archivo(archivo)
        except FileNotFoundError:
            print("SKIP: " + archivo + " (no existe)")
            continue
        if encontrados:
            print("FALLA: " + archivo)
            for ln, texto in encontrados:
                print("  linea " + str(ln) + ": " + texto[:80])
            fallos += len(encontrados)
        else:
            print("OK: " + archivo)

    print()
    if fallos == 0:
        print("GUARDIAN OK: 0 literales prohibidos en archivos migrados")
        return 0
    print(str(fallos) + " LITERALES PROHIBIDOS ENCONTRADOS")
    return 1


if __name__ == "__main__":
    sys.exit(main())
