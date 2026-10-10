#!/usr/bin/env python3
"""cualificar_runtime.py - Tests A/B/C/D del memo 76.

Uso:
    python3 cualificar_runtime.py --test A
    python3 cualificar_runtime.py --test B
    python3 cualificar_runtime.py --test C
    python3 cualificar_runtime.py --test D
    python3 cualificar_runtime.py --all
"""
import argparse
import json
import subprocess
import sys
import time
import urllib.request
from datetime import datetime

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODELO = "qwen2.5-coder:1.5b"

S_STAR_STATE = {
    "pos_x": 0.0, "pos_z": 0.0,
    "hdg": 90.0, "sog": 3.0,
    "meta_x": 100.0, "meta_z": 100.0,
    "viento_kn": 0.0, "viento_dir": 0.0,
}

S_STAR_PROMPT = """Sos el timonel de un velero. Mision: llegar a la meta.

ESTADO ACTUAL:
- Posicion: (0.0, 0.0)
- Meta: (100.0, 100.0)
- Distancia a meta: 141.4 metros
- Heading (proa): 90.0 grados
- Rumbo hacia la meta: 45.0 grados
- Desvio actual: 45.0 grados
- Velocidad: 3.00 nudos

ACCIONES DISPONIBLES:
- corregir_rumbo: girar la proa a un angulo absoluto (0=norte, 90=este). Parametro: grados (0-360).
- ir_a_punto: navegar hacia coordenadas. Parametro: [x, z].
- frenar: reducir velocidad hasta aproximadamente 0.3 nudos.
- terminar: declarar fin de mision. Valida SOLO si la distancia a meta es menor a 15 metros.

TAREA:
Analiza la situacion y elegi la accion que mejor contribuya a llegar a la meta.

Responde UNICAMENTE con JSON, sin texto adicional. Formato:
{"accion": "<accion>", "parametro": <parametro o null>}
"""

PREDECESORES = {
    "neutral": "hola, como estas?",
    "dominio_A": "Sos un timonel. Decime que es corregir_rumbo en una palabra.",
    "dominio_B": "Sos un timonel. Decime que es ir_a_punto en una palabra.",
    "largo": "Explica en pocas palabras la diferencia entre heading, rumbo y course over ground en navegacion.",
}


def consultar_raw(prompt, num_predict=80, timeout=120):
    """Llama a Ollama y devuelve el JSON completo (con metadata)."""
    data = json.dumps({
        "model": MODELO,
        "prompt": prompt,
        "stream": False,
        "options": {"num_ctx": 2048, "temperature": 0, "seed": 555, "num_predict": num_predict, "num_batch": 512},
    }).encode()
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except Exception as e:
        return {"error": str(e)}


def stop_modelo():
    subprocess.run(["ollama", "stop", MODELO], capture_output=True, timeout=15)
    time.sleep(1.0)


def extraer_decision(response):
    """Extrae (accion, parametro) del texto de respuesta."""
    import re
    texto = response.strip()
    if texto.startswith("```"):
        lineas = texto.split(chr(10))
        lineas = [l for l in lineas if not l.strip().startswith("```")]
        texto = chr(10).join(lineas).strip()
    i = texto.find("{")
    j = texto.rfind("}")
    if i == -1 or j == -1 or j <= i:
        return ("sin_json", None)
    try:
        obj = json.loads(texto[i:j+1])
        return (obj.get("accion", "?"), obj.get("parametro"))
    except Exception:
        return ("json_invalido", None)


def test_A(n=5):
    """Repetibilidad pura de S*."""
    print("=== TEST A: Repetibilidad pura de S* (n=" + str(n) + ") ===")
    resultados = []
    for i in range(n):
        r = consultar_raw(S_STAR_PROMPT)
        if "error" in r:
            print("  [" + str(i+1) + "] ERROR: " + r["error"])
            continue
        accion, param = extraer_decision(r.get("response", ""))
        cached = r.get("prompt_eval_cached_count", -1)
        load_ms = r.get("load_duration", 0) / 1e6
        eval_ms = r.get("eval_duration", 0) / 1e6
        print("  [" + str(i+1) + "] accion=" + accion + " param=" + str(param) + " cached=" + str(cached) + " load_ms=" + str(round(load_ms, 1)) + " eval_ms=" + str(round(eval_ms, 1)))
        resultados.append({"accion": accion, "parametro": param, "cached": cached, "load_ms": round(load_ms, 1)})
    unicas = set((r["accion"], str(r["parametro"])) for r in resultados)
    print("  respuestas distintas: " + str(len(unicas)) + "/" + str(len(resultados)))
    return {"test": "A", "n": n, "resultados": resultados, "unicas": len(unicas)}


def test_B(n_por_predecesor=3):
    """Sensibilidad de S* al predecesor."""
    print("=== TEST B: Sensibilidad al predecesor ===")
    resultados = {}
    for nombre, predecesor in PREDECESORES.items():
        print("  --- predecesor: " + nombre + " ---")
        corridas = []
        for i in range(n_por_predecesor):
            # Correr el predecesor (para cargar su estado)
            consultar_raw(predecesor, num_predict=20)
            # Correr S*
            r = consultar_raw(S_STAR_PROMPT)
            if "error" in r:
                print("    [" + str(i+1) + "] ERROR: " + r["error"])
                continue
            accion, param = extraer_decision(r.get("response", ""))
            cached = r.get("prompt_eval_cached_count", -1)
            print("    [" + str(i+1) + "] S*: accion=" + accion + " param=" + str(param) + " cached=" + str(cached))
            corridas.append({"accion": accion, "parametro": param, "cached": cached})
        resultados[nombre] = corridas
    return {"test": "B", "por_predecesor": n_por_predecesor, "resultados": resultados}


def test_C(n_por_predecesor=3):
    """Igual que Test B, pero con ollama stop entre corridas."""
    print("=== TEST C: ollama stop entre corridas ===")
    resultados = {}
    for nombre, predecesor in PREDECESORES.items():
        print("  --- predecesor: " + nombre + " ---")
        corridas = []
        for i in range(n_por_predecesor):
            stop_modelo()
            consultar_raw(predecesor, num_predict=20)
            stop_modelo()
            r = consultar_raw(S_STAR_PROMPT)
            if "error" in r:
                print("    [" + str(i+1) + "] ERROR: " + r["error"])
                continue
            accion, param = extraer_decision(r.get("response", ""))
            cached = r.get("prompt_eval_cached_count", -1)
            load_ms = r.get("load_duration", 0) / 1e6
            print("    [" + str(i+1) + "] S*: accion=" + accion + " param=" + str(param) + " cached=" + str(cached) + " load_ms=" + str(round(load_ms, 1)))
            corridas.append({"accion": accion, "parametro": param, "cached": cached, "load_ms": round(load_ms, 1)})
        resultados[nombre] = corridas
    return {"test": "C", "por_predecesor": n_por_predecesor, "resultados": resultados}


def test_D(n=20):
    """20 corridas de S* con ollama stop + recarga."""
    print("=== TEST D: Regimen a lo largo del tiempo (n=" + str(n) + ") ===")
    resultados = []
    for i in range(n):
        stop_modelo()
        r = consultar_raw(S_STAR_PROMPT)
        if "error" in r:
            print("  [" + str(i+1) + "] ERROR: " + r["error"])
            continue
        accion, param = extraer_decision(r.get("response", ""))
        load_ms = r.get("load_duration", 0) / 1e6
        print("  [" + str(i+1) + "/" + str(n) + "] accion=" + accion + " param=" + str(param) + " load_ms=" + str(round(load_ms, 1)))
        resultados.append({"accion": accion, "parametro": param, "load_ms": round(load_ms, 1)})
    unicas = set((r["accion"], str(r["parametro"])) for r in resultados)
    print("  respuestas distintas: " + str(len(unicas)) + "/" + str(len(resultados)))
    return {"test": "D", "n": n, "resultados": resultados, "unicas": len(unicas)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", choices=["A", "B", "C", "D"])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--out", default="cualificacion_runtime_resultado.json")
    args = ap.parse_args()

    if not args.all and not args.test:
        ap.error("Elegi --test A/B/C/D o --all")

    resultados = {"fecha": datetime.now().isoformat(), "modelo": MODELO}
    t0 = time.time()

    if args.all or args.test == "A":
        resultados["A"] = test_A()
    if args.all or args.test == "B":
        resultados["B"] = test_B()
    if args.all or args.test == "C":
        resultados["C"] = test_C()
    if args.all or args.test == "D":
        resultados["D"] = test_D()

    resultados["duracion_s"] = round(time.time() - t0, 1)

    with open(args.out, "w") as f:
        json.dump(resultados, f, indent=2, default=str)
    print("")
    print("[OK] resultados guardados en " + args.out)
    print("[OK] duracion total: " + str(resultados["duracion_s"]) + "s")


if __name__ == "__main__":
    main()
