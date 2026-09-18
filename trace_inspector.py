#!/usr/bin/env python3
"""
trace_inspector.py — Analiza un trace.jsonl de DSH y extrae métricas.

Uso:
  python3 trace_inspector.py <ruta_al_trace.jsonl>
  python3 trace_inspector.py <ruta_a_carpeta_con_traces>
"""
import sys, json
from collections import Counter
from pathlib import Path


def analizar_un_trace(trace_path, verbose=True):
    eventos = []
    with open(trace_path) as f:
        for linea in f:
            try:
                eventos.append(json.loads(linea))
            except json.JSONDecodeError:
                pass

    if not eventos:
        return None

    herramientas = Counter()
    archivos_leidos = set()
    archivos_escritos = set()
    comandos = []
    tests_ejecutados = []

    for ev in eventos:
        if ev.get("type") != "tool/call":
            continue
        data = ev.get("data", {})
        nombre = data.get("name", "?")
        herramientas[nombre] += 1

        # arguments es un STRING JSON, hay que parsearlo
        args_raw = data.get("arguments", "{}")
        try:
            args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
        except (json.JSONDecodeError, TypeError):
            args = {}

        if not isinstance(args, dict):
            continue

        # read: {file_path: "..."} o {path: "..."}
        if nombre == "read":
            p = args.get("file_path") or args.get("path") or args.get("file")
            if p:
                archivos_leidos.add(p)

        # write / edit / str_replace: {file_path: "..."}
        if nombre in ("write", "edit", "str_replace", "apply_patch"):
            p = args.get("file_path") or args.get("path") or args.get("file")
            if p:
                archivos_escritos.add(p)

        # bash: {command: "..."}
        if nombre == "bash":
            cmd = args.get("command", "")
            if cmd:
                comandos.append(cmd[:150])
                cmd_lower = cmd.lower()
                if "test" in cmd_lower or "pytest" in cmd_lower or "unittest" in cmd_lower:
                    tests_ejecutados.append(cmd[:150])

        # grep: {pattern, path}
        if nombre == "grep":
            pat = args.get("pattern", "")
            path = args.get("path", "")
            comandos.append(f"grep {pat!r} en {path}")

    tiempos = [ev.get("time") for ev in eventos if ev.get("time")]
    duracion_ms = (tiempos[-1] - tiempos[0]) if len(tiempos) >= 2 else 0

    tipos = Counter(ev.get("type", "unknown") for ev in eventos)

    resultado = {
        "trace": trace_path.name,
        "eventos": len(eventos),
        "duracion_ms": duracion_ms,
        "herramientas": dict(herramientas),
        "archivos_leidos": sorted(archivos_leidos),
        "archivos_escritos": sorted(archivos_escritos),
        "comandos": comandos,
        "tests": tests_ejecutados,
        "tipos": dict(tipos),
    }

    if verbose:
        print("=" * 60)
        print(f"TRACE: {trace_path.name}")
        print("=" * 60)
        print(f"Eventos: {len(eventos)}  |  Duración: {duracion_ms} ms ({duracion_ms/1000:.1f}s)")
        print()
        print("--- HERRAMIENTAS ---")
        for h, c in herramientas.most_common():
            print(f"  {h}: {c}")
        print()
        print(f"--- ARCHIVOS LEÍDOS ({len(archivos_leidos)}) ---")
        for a in sorted(archivos_leidos)[:15]:
            print(f"  {a}")
        if len(archivos_leidos) > 15:
            print(f"  ... +{len(archivos_leidos)-15}")
        print()
        print(f"--- ARCHIVOS ESCRITOS ({len(archivos_escritos)}) ---")
        for a in sorted(archivos_escritos):
            print(f"  {a}")
        print()
        print(f"--- COMANDOS ({len(comandos)}) ---")
        for c in comandos[:10]:
            print(f"  $ {c}")
        if len(comandos) > 10:
            print(f"  ... +{len(comandos)-10}")
        print()
        print(f"--- TESTS ({len(tests_ejecutados)}) ---")
        for t in tests_ejecutados:
            print(f"  $ {t}")
        print()

    return resultado


def analizar_carpeta(carpeta):
    """Analiza todos los trace.jsonl en una carpeta de runs."""
    carpeta = Path(carpeta)
    traces = sorted(carpeta.glob("DSH_RUN_*/trace.jsonl"))
    if not traces:
        print(f"No hay traces en {carpeta}")
        return

    print("=" * 70)
    print(f"ANÁLISIS GLOBAL: {len(traces)} runs")
    print("=" * 70)
    print()
    print(f"{'Ensayo':<8} {'Eventos':<10} {'Duración':<12} {'Herramientas':<30} {'Archivos E'} ")
    print("-" * 70)

    for t in traces:
        r = analizar_un_trace(t, verbose=False)
        if not r:
            continue
        ensayo = t.parent.name.split("_")[2]
        hrs = ", ".join(f"{k}:{v}" for k, v in list(r["herramientas"].items())[:3])
        print(f"{ensayo:<8} {r['eventos']:<10} {r['duracion_ms']/1000:>5.1f}s      {hrs:<30} {len(r['archivos_escritos'])}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 trace_inspector.py <ruta>")
        print("     (ruta puede ser un trace.jsonl o una carpeta de runs)")
        sys.exit(1)

    ruta = Path(sys.argv[1])
    if ruta.is_dir():
        analizar_carpeta(ruta)
    else:
        analizar_un_trace(ruta)
