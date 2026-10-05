#!/usr/bin/env python3
"""
memoria.py - Memoria externa del agente Timonel.

Guarda cada corrida y cada decision en una base SQLite local.
Permite recuperar decisiones similares a la situacion actual
para inyectarlas en el prompt de Qwen.
"""

import json
import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DB_PATH_DEFAULT = Path(__file__).parent / "memoria.db"


def conectar(db_path: Path = DB_PATH_DEFAULT) -> sqlite3.Connection:
    """Abre la base y crea las tablas si no existen."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS corridas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            meta_x REAL NOT NULL,
            meta_z REAL NOT NULL,
            pos_inicial_x REAL NOT NULL,
            pos_inicial_z REAL NOT NULL,
            hdg_inicial REAL NOT NULL,
            resultado TEXT NOT NULL,
            dist_final REAL NOT NULL,
            t_total REAL NOT NULL,
            num_pasos INTEGER NOT NULL,
            modelo_llm TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS decisiones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            corrida_id INTEGER NOT NULL,
            paso_num INTEGER NOT NULL,
            t REAL NOT NULL,
            pos_x REAL NOT NULL,
            pos_z REAL NOT NULL,
            hdg REAL NOT NULL,
            sog REAL NOT NULL,
            dist_meta REAL NOT NULL,
            desvio REAL NOT NULL,
            decision TEXT NOT NULL,
            parametro TEXT,
            exito INTEGER NOT NULL,
            resultado_corrida TEXT NOT NULL,
            FOREIGN KEY (corrida_id) REFERENCES corridas(id)
        );

        CREATE INDEX IF NOT EXISTS idx_dec_dist_desvio
            ON decisiones(dist_meta, desvio);

        CREATE INDEX IF NOT EXISTS idx_dec_resultado
            ON decisiones(resultado_corrida);
    """)
    return conn


def guardar_corrida_y_decisiones(conn: sqlite3.Connection, corrida_dict: dict) -> int:
    """Guarda una corrida y todas sus decisiones. Retorna el id de la corrida."""
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO corridas (
            fecha, meta_x, meta_z, pos_inicial_x, pos_inicial_z,
            hdg_inicial, resultado, dist_final, t_total, num_pasos, modelo_llm
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        corrida_dict["fecha"],
        corrida_dict["meta_x"],
        corrida_dict["meta_z"],
        corrida_dict["pos_inicial"][0],
        corrida_dict["pos_inicial"][1],
        corrida_dict["hdg_inicial"],
        corrida_dict["resultado"],
        corrida_dict["dist_final"],
        corrida_dict["t_total"],
        corrida_dict["num_pasos"],
        corrida_dict["modelo_llm"],
    ))
    corrida_id = cur.lastrowid

    for paso in corrida_dict["pasos"]:
        # Calcular desvio actual en el momento de la decision
        meta_x = corrida_dict["meta_x"]
        meta_z = corrida_dict["meta_z"]
        dx = meta_x - paso["pos_x"]
        dz = meta_z - paso["pos_z"]
        rumbo_hacia = math.degrees(math.atan2(dx, -dz)) % 360.0
        desvio = abs((rumbo_hacia - paso["hdg"] + 540) % 360 - 180)

        # Guardar parametro como string (puede ser numero o lista)
        parametro = paso.get("argumento", "")
        # Semantica: 'exito' del paso = la corrida fue exitosa.
        # La receta puede haber timeoutado internamente pero el barco igual llego.
        exito_int = 1 if corrida_dict["resultado"] == "LLEGO" else 0

        cur.execute("""
            INSERT INTO decisiones (
                corrida_id, paso_num, t, pos_x, pos_z, hdg, sog,
                dist_meta, desvio, decision, parametro, exito, resultado_corrida
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            corrida_id, 0, paso["t"], paso["pos_x"], paso["pos_z"],
            paso["hdg"], paso["sog"], paso["dist_meta"], desvio,
            paso["decision"], parametro, exito_int, corrida_dict["resultado"],
        ))

    conn.commit()
    return corrida_id


def estadisticas(conn: sqlite3.Connection) -> dict:
    """Devuelve estadisticas basicas de la memoria."""
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM corridas")
    n_corridas = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM decisiones")
    n_decisiones = cur.fetchone()[0]
    cur.execute("SELECT resultado, COUNT(*) FROM corridas GROUP BY resultado")
    por_resultado = dict(cur.fetchall())
    return {
        "corridas": n_corridas,
        "decisiones": n_decisiones,
        "por_resultado": por_resultado,
    }


if __name__ == "__main__":
    conn = conectar()
    est = estadisticas(conn)
    print("=== Estado de la memoria ===")
    print(f"  Corridas:   {est['corridas']}")
    print(f"  Decisiones: {est['decisiones']}")
    print(f"  Por resultado: {est['por_resultado']}")
    conn.close()


# ============================================================
# RECUPERACION DE EXPERIENCIAS SIMILARES
# ============================================================

@dataclass
class Experiencia:
    """Una decision pasada recuperada de la memoria."""
    dist_meta: float
    desvio: float
    sog: float
    decision: str
    parametro: str
    exito: bool
    resultado_corrida: str
    score_similitud: float


def _score_similitud(d_actual: float, desv_actual: float, sog_actual: float,
                     d_exp: float, desv_exp: float, sog_exp: float) -> float:
    """
    Score de similitud entre dos situaciones. Menor = mas parecido.

    Pesa mas la distancia (escala mayor) y el desvio (afecta decision).
    Normaliza para que las tres dimensiones cuenten.
    """
    # Normalizar cada dimension a un rango de 0-1 aprox
    # Distancias tipicas: 0-300m -> dividir por 300
    # Desvio tipico: 0-180 grados -> dividir por 180
    # SOG tipico: 0-5 kn -> dividir por 5
    d_dist = abs(d_actual - d_exp) / 300.0
    d_desv = abs(desv_actual - desv_exp) / 180.0
    d_sog = abs(sog_actual - sog_exp) / 5.0
    # Score combinado (peso mayor a distancia y desvio)
    return 2.0 * d_dist + 2.0 * d_desv + 0.5 * d_sog


def recuperar_similares(conn: sqlite3.Connection,
                        dist_meta: float, desvio: float, sog: float,
                        n: int = 5,
                        solo_exitos: bool = True,
                        umbral_desvio_deg: float = 45.0,
                        umbral_dist_m: float = 60.0) -> list:
    """
    Recupera las N decisiones mas parecidas a la situacion actual.

    Estrategia en cascada:
    1. Filtro duro: mismo signo de desvio + diferencia de desvio y distancia
       dentro de umbrales. Si hay resultados, devuelve los mejores.
    2. Fallback 1: solo mismo signo de desvio.
    3. Fallback 2: todas las filas (score general).
    """
    cur = conn.cursor()
    if solo_exitos:
        cur.execute("""
            SELECT dist_meta, desvio, sog, decision, parametro, exito, resultado_corrida
            FROM decisiones
            WHERE resultado_corrida = 'LLEGO'
            LIMIT 5000
        """)
    else:
        cur.execute("""
            SELECT dist_meta, desvio, sog, decision, parametro, exito, resultado_corrida
            FROM decisiones
            LIMIT 5000
        """)
    filas = cur.fetchall()

    def armar(f):
        score = _score_similitud(
            dist_meta, desvio, sog,
            f["dist_meta"], f["desvio"], f["sog"],
        )
        return Experiencia(
            dist_meta=f["dist_meta"],
            desvio=f["desvio"],
            sog=f["sog"],
            decision=f["decision"],
            parametro=f["parametro"] or "",
            exito=bool(f["exito"]),
            resultado_corrida=f["resultado_corrida"],
            score_similitud=score,
        )

    # Etapa 1: filtro duro
    candidatos = []
    for f in filas:
        mismo_signo = (desvio * f["desvio"]) >= 0
        dif_desv = abs(desvio - f["desvio"])
        dif_dist = abs(dist_meta - f["dist_meta"])
        if mismo_signo and dif_desv < umbral_desvio_deg and dif_dist < umbral_dist_m:
            candidatos.append(armar(f))

    if candidatos:
        candidatos.sort(key=lambda e: e.score_similitud)
        return candidatos[:n]

    # Etapa 2: fallback sin filtros (solo si etapa 1 no dio nada)
    # NOTA: quitamos la etapa de "mismo signo" porque el corpus esta sesgado
    # hacia desvios positivos y esa etapa devolvia ruido.
    for f in filas:
        candidatos.append(armar(f))
    candidatos.sort(key=lambda e: e.score_similitud)
    return candidatos[:n]


def filtrar_por_consenso(experiencias: list, minimo_ratio: float = 0.6) -> list:
    """
    Filtra una lista de experiencias para quedarse con la decision mayoritaria
    si tiene al menos `minimo_ratio` del total.

    Ejemplo: si 3 de 5 dicen ir_a_punto, ratio 0.6, devuelve solo las 3.
    Si 2-1-1-1, ninguna tiene 0.6, devuelve lista vacia (sin consenso).
    """
    if not experiencias:
        return []
    from collections import Counter
    conteo = Counter(e.decision for e in experiencias)
    total = len(experiencias)
    decision_top, n_top = conteo.most_common(1)[0]
    if n_top / total >= minimo_ratio:
        return [e for e in experiencias if e.decision == decision_top]
    return []


def formatear_experiencias_para_prompt(experiencias: list) -> str:
    """
    Convierte una lista de Experiencias en texto para inyectar en el prompt.
    Devuelve string vacio si la lista esta vacia.
    """
    if not experiencias:
        return ""

    lineas = ["EXPERIENCIAS PREVIAS (situaciones parecidas):"]
    for i, exp in enumerate(experiencias, 1):
        lineas.append(
            f"  {i}. [dist={exp.dist_meta:.0f}m desvio={exp.desvio:.0f}deg sog={exp.sog:.1f}kn] "
            f"-> {exp.decision}({exp.parametro}) [exito={exp.exito}]"
        )
    lineas.append("")
    lineas.append("Usa estas experiencias como referencia, no como regla. "
                  "Si la situacion actual es parecida, considera lo que funciono antes.")
    return "\n".join(lineas)
