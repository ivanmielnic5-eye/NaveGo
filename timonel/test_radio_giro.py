#!/usr/bin/env python3
"""test_radio_giro.py - Audita si el oraculo esta en lo correcto al pedir
corregir_rumbo en los casos donde el modelo prefirio ir_a_punto.

Idea del Director: el radio de giro es grande y a corta distancia puede
hacer que corregir_rumbo ALEJE al barco en vez de acercarlo.

Para cada caso problematico:
1. Simular 60s con corregir_rumbo (hacia la meta)
2. Simular 60s con ir_a_punto (hacia la meta)
3. Comparar distancia final y si llego a la meta
"""
import math
import sys
sys.path.insert(0, ".")

from simulador_polaris import Barco
from recetas_navegacion import corregir_rumbo, ir_a_punto


# Los casos donde verdad=corregir_rumbo y pred=ir_a_punto (del analisis)
CASOS = [
    {"dist": 18.2,  "desv": 46.4, "sog": 3.0},
    {"dist": 173.0, "desv": 82.5, "sog": 3.0},
    {"dist": 113.5, "desv": 76.8, "sog": 3.0},
    {"dist": 17.4,  "desv": 19.1, "sog": 3.0},
    {"dist": 18.0,  "desv": 13.0, "sog": 3.0},
    {"dist": 19.2,  "desv": 61.0, "sog": 3.0},
    {"dist": 22.6,  "desv": 41.6, "sog": 3.0},
    {"dist": 17.9,  "desv": 40.6, "sog": 3.0},
    {"dist": 29.9,  "desv": 30.8, "sog": 3.0},
]


def crear_barco(dist, desv, sog):
    """Crea un barco con posicion (0,0), meta al norte, y desvio dado.
    Asume meta en (0, -dist) => rumbo_hacia_meta = 0 (norte).
    Entonces hdg = desv (positivo = hacia el este)."""
    b = Barco()
    b.pos_x = 0.0
    b.pos_z = 0.0
    # Meta al norte
    meta_x = 0.0
    meta_z = -dist
    # Heading = desvio (positivo), porque rumbo_hacia_meta = 0
    b.yaw = math.radians(desv)
    # SOG en direccion del heading
    sog_ms = sog / 1.94384449
    b.vel_x = math.sin(b.yaw) * sog_ms
    b.vel_z = -math.cos(b.yaw) * sog_ms
    return b, meta_x, meta_z


def simular_accion(barco_base, meta_x, meta_z, accion, timeout_s=60.0):
    """Simula una accion y devuelve dist final, exito, tiempo."""
    import copy
    b = copy.deepcopy(barco_base)

    if accion == "corregir_rumbo":
        dx = meta_x - b.pos_x
        dz = meta_z - b.pos_z
        rumbo = math.degrees(math.atan2(dx, -dz)) % 360.0
        exito, detalle = corregir_rumbo(b, objetivo_deg=rumbo, timeout_s=timeout_s)
    elif accion == "ir_a_punto":
        exito, detalle = ir_a_punto(b, meta_x, meta_z, tol_dist=15.0, timeout_s=timeout_s)
    else:
        return None

    dist_final = math.sqrt((b.pos_x - meta_x)**2 + (b.pos_z - meta_z)**2)
    return {
        "accion": accion,
        "exito": exito,
        "dist_final": round(dist_final, 2),
        "tiempo": round(b.t, 1),
        "pos_final": (round(b.pos_x, 2), round(b.pos_z, 2)),
    }


def main():
    print("=== TEST: radio de giro en casos problematicos ===\n")

    for i, caso in enumerate(CASOS):
        dist = caso["dist"]
        desv = caso["desv"]
        sog = caso["sog"]

        b, mx, mz = crear_barco(dist, desv, sog)

        r_corregir = simular_accion(b, mx, mz, "corregir_rumbo", timeout_s=60.0)
        r_ir_a_punto = simular_accion(b, mx, mz, "ir_a_punto", timeout_s=60.0)

        print(f"--- Caso {i+1}: dist={dist}m desv={desv}° sog={sog}kn ---")
        print(f"  corregir_rumbo: exito={r_corregir['exito']} dist_final={r_corregir['dist_final']}m t={r_corregir['tiempo']}s")
        print(f"  ir_a_punto:     exito={r_ir_a_punto['exito']} dist_final={r_ir_a_punto['dist_final']}m t={r_ir_a_punto['tiempo']}s")

        if r_corregir["dist_final"] < r_ir_a_punto["dist_final"]:
            print(f"  GANADOR: corregir_rumbo (oraculo tiene razon)")
        elif r_corregir["dist_final"] > r_ir_a_punto["dist_final"]:
            print(f"  GANADOR: ir_a_punto (EL MODELO TIENE RAZON)")
        else:
            print(f"  EMPATE")
        print()


if __name__ == "__main__":
    main()
