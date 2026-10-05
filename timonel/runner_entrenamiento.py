#!/usr/bin/env python3
"""
runner_entrenamiento.py - Corre N corridas del agente en secuencia.

Varía las condiciones (meta aleatoria), guarda cada corrida en JSON,
y al final imprime un resumen estadístico.

Uso:
    python3 runner_entrenamiento.py --n 20
    python3 runner_entrenamiento.py --n 100 --llm   # con Qwen
"""

import argparse
import json
import math
import random
import time
from datetime import datetime
from pathlib import Path

from timonel_python import AgenteTimonel, guardar_corrida
from memoria import conectar, guardar_corrida_y_decisiones, estadisticas


def generar_meta(rng: random.Random) -> tuple:
    """Genera una meta aleatoria a 100-250m del origen, en cualquier direccion."""
    distancia = rng.uniform(100.0, 250.0)
    angulo = rng.uniform(0.0, 360.0)
    mx = distancia * math.sin(math.radians(angulo))
    mz = -distancia * math.cos(math.radians(angulo))
    return round(mx, 1), round(mz, 1)


def generar_mision(rng: random.Random, n_metas: int = 2) -> list:
    """Genera una lista de N metas aleatorias. Para misiones tipo 'recoger y llevar'."""
    metas = []
    for i in range(n_metas):
        dist = rng.uniform(80.0, 220.0)
        ang = rng.uniform(0.0, 360.0)
        mx = round(dist * math.sin(math.radians(ang)), 1)
        mz = round(-dist * math.cos(math.radians(ang)), 1)
        metas.append((mx, mz))
    return metas


def correr_batch(n_corridas: int, usar_llm: bool, dir_salida: Path,
                 rng_seed: int = None, timeout_s: float = 300.0,
                 usar_memoria: bool = False, viento_max_kn: float = 0.0,
                 viento_variar: bool = False, viento_periodo_s: float = 20.0,
                 n_metas: int = 1):
    """Corre N corridas y guarda cada una."""
    rng = random.Random(rng_seed) if rng_seed is not None else random.Random()
    dir_salida.mkdir(parents=True, exist_ok=True)

    # Conexion a la memoria (SQLite)
    conn = conectar()
    est_antes = estadisticas(conn)
    print(f"[runner] Memoria antes: {est_antes['corridas']} corridas, {est_antes['decisiones']} decisiones")

    resultados = []
    t_inicio_batch = time.time()

    print(f"[runner] Arrancando batch de {n_corridas} corridas")
    print(f"[runner] Usar LLM: {usar_llm}")
    print(f"[runner] Salida: {dir_salida}")
    print(f"[runner] Seed: {rng_seed if rng_seed is not None else 'aleatorio'}")
    print()

    for i in range(n_corridas):
        if n_metas == 1:
            meta_x, meta_z = generar_meta(rng)
            metas = None
            meta_para_reporte = (meta_x, meta_z)
        else:
            metas = generar_mision(rng, n_metas=n_metas)
            meta_x, meta_z = metas[0]
            meta_para_reporte = metas[-1]  # la meta final

        agente = AgenteTimonel(
            meta_x=meta_x, meta_z=meta_z, metas=metas,
            timeout_s=timeout_s, usar_llm=usar_llm,
            conn=conn if usar_memoria else None,
            max_pasos=15,
        )

        # Viento para esta corrida
        viento_int = 0.0
        viento_dir = 0.0
        if viento_variar and viento_max_kn > 0.0:
            # Viento variable: cambia cada viento_periodo_s segundos
            agente.barco.viento_variar = True
            agente.barco.viento_max_kn = viento_max_kn
            agente.barco.viento_periodo_s = viento_periodo_s
            agente.barco.viento_seed = rng.randint(0, 2**31 - 1)
        elif viento_max_kn > 0.0:
            # Viento constante aleatorio
            viento_int = rng.uniform(0.0, viento_max_kn)
            viento_dir = rng.uniform(0.0, 360.0)
            agente.barco.viento_intensidad_kn = viento_int
            agente.barco.viento_direccion_deg = viento_dir

        corrida = agente.correr(verbose=False)

        ruta = guardar_corrida(corrida, dir_salida)
        # Guardar tambien en la memoria SQLite
        try:
            from dataclasses import asdict as _asdict
            guardar_corrida_y_decisiones(conn, _asdict(corrida))
        except Exception as e:
            print(f"  [memoria] error guardando: {e}")
        resultados.append({
            "n": i + 1,
            "meta": (meta_x, meta_z),
            "viento_kn": round(viento_int, 1),
            "viento_dir": round(viento_dir, 0),
            "resultado": corrida.resultado,
            "dist_final": corrida.dist_final,
            "t_total": corrida.t_total,
            "num_pasos": corrida.num_pasos,
            "llm_fallos": agente.llm_fallos if usar_llm else 0,
        })

        info_viento = ""
        if viento_max_kn > 0.0:
            info_viento = f" viento={viento_int:>4.1f}kn/{viento_dir:>3.0f}deg"
        info_metas = ""
        if n_metas > 1:
            info_metas = f" metas={agente.metas_alcanzadas}/{n_metas}"
        print(f"[{i+1:>3d}/{n_corridas}] meta=({meta_para_reporte[0]:>6.1f},{meta_para_reporte[1]:>6.1f})"
              f"{info_viento}{info_metas} -> {corrida.resultado:>8s} dist={corrida.dist_final:>6.1f}m "
              f"t={corrida.t_total:>5.1f}s pasos={corrida.num_pasos}")

    t_fin_batch = time.time()
    duracion_batch = t_fin_batch - t_inicio_batch

    exitos = sum(1 for r in resultados if r["resultado"] == "LLEGO")
    timeouts = sum(1 for r in resultados if r["resultado"] == "TIMEOUT")
    fracasos = sum(1 for r in resultados if r["resultado"] == "FRACASO")
    dist_prom_exito = (
        sum(r["dist_final"] for r in resultados if r["resultado"] == "LLEGO") / exitos
        if exitos > 0 else 0.0
    )
    time_prom_exito = (
        sum(r["t_total"] for r in resultados if r["resultado"] == "LLEGO") / exitos
        if exitos > 0 else 0.0
    )
    total_fallos_llm = sum(r["llm_fallos"] for r in resultados)

    resumen = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "n_corridas": n_corridas,
        "usar_llm": usar_llm,
        "usar_memoria": usar_memoria,
        "viento_max_kn": viento_max_kn,
        "seed": rng_seed,
        "duracion_real_seg": round(duracion_batch, 1),
        "exitos": exitos,
        "timeouts": timeouts,
        "fracasos": fracasos,
        "tasa_exito": round(exitos / n_corridas, 3),
        "dist_promedio_exitos": round(dist_prom_exito, 1),
        "tiempo_promedio_exitos": round(time_prom_exito, 1),
        "fallos_llm_totales": total_fallos_llm,
        "detalles": resultados,
    }

    print()
    print("=" * 60)
    print(" RESUMEN DEL BATCH")
    print("=" * 60)
    print(f"  Corridas:          {n_corridas}")
    print(f"  Exitos:            {exitos} ({100*exitos/n_corridas:.1f}%)")
    print(f"  Timeouts:          {timeouts}")
    print(f"  Fracasos:          {fracasos}")
    print(f"  Dist prom exito:   {dist_prom_exito:.1f} m")
    print(f"  Tiempo prom exito: {time_prom_exito:.1f} s (simulados)")
    print(f"  Fallos LLM:        {total_fallos_llm}")
    print(f"  Duracion real:     {duracion_batch:.1f} s")
    print()

    nombre_resumen = f"resumen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    ruta_resumen = dir_salida / nombre_resumen
    with ruta_resumen.open("w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)
    print(f"[runner] Resumen guardado en: {ruta_resumen}")

    est_despues = estadisticas(conn)
    print(f"[runner] Memoria despues: {est_despues['corridas']} corridas, {est_despues['decisiones']} decisiones")
    conn.close()

    return resumen


def main():
    parser = argparse.ArgumentParser(description="Runner de entrenamiento de Timonel")
    parser.add_argument("--n", type=int, default=10, help="Cantidad de corridas")
    parser.add_argument("--llm", action="store_true", help="Usar Qwen para decidir")
    parser.add_argument("--seed", type=int, default=None, help="Semilla para reproducibilidad")
    parser.add_argument("--memoria", action="store_true",
                        help="Consultar la memoria SQLite para inyectar experiencias")
    parser.add_argument("--viento-max", type=float, default=0.0,
                        help="Intensidad maxima de viento aleatorio (nudos). 0 = sin viento.")
    parser.add_argument("--viento-variable", action="store_true",
                        help="El viento cambia cada N segundos (mas dificil)")
    parser.add_argument("--viento-periodo", type=float, default=20.0,
                        help="Cada cuantos segundos cambia el viento variable")
    parser.add_argument("--n-metas", type=int, default=1,
                        help="Cantidad de metas por corrida (misiones multi-punto)")
    parser.add_argument("--timeout", type=float, default=300.0, help="Timeout por corrida (s)")
    parser.add_argument("--dir", type=str, default=None, help="Directorio de salida")
    args = parser.parse_args()

    if args.dir:
        dir_salida = Path(args.dir)
    else:
        dir_salida = Path.home() / "navego_recuperado" / "timonel" / "corridas"

    correr_batch(
        n_corridas=args.n,
        usar_llm=args.llm,
        dir_salida=dir_salida,
        rng_seed=args.seed,
        timeout_s=args.timeout,
        usar_memoria=args.memoria,
        viento_max_kn=args.viento_max,
        viento_variar=args.viento_variable,
        viento_periodo_s=args.viento_periodo,
        n_metas=args.n_metas,
    )


if __name__ == "__main__":
    main()
