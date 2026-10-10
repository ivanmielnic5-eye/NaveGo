#!/usr/bin/env python3
"""
oraculo.py - Oraculo myopic para evaluar decisiones (version memo 61).

Multi-horizonte. Metricas separadas: boundary_violation + progreso.
Sin capa de continuacion. Near-tie definido externamente.
"""

import copy
import math
from dataclasses import dataclass

from simulador_polaris import Barco, DT
from recetas_navegacion import corregir_rumbo, ir_a_punto, frenar


HORIZONTES_S = [5.0, 15.0, 30.0, 45.0]
RADIO_BOUNDARY_M = 500.0
RECETAS_DISPONIBLES = ["corregir_rumbo", "ir_a_punto", "frenar", "terminar"]


@dataclass
class ResultadoReceta:
    receta: str
    seguro: bool
    progreso_por_horizonte: dict
    alineacion_deg: float
    dist_final_m: float
    pos_final: tuple
    boundary_violation: bool
    mission_complete: bool = False
    progreso_medio: float = 0.0
    margen_vs_segunda: float = 0.0
    parametro: object = None
    error: str = ""


def _distancia_a(b, mx, mz):
    return math.sqrt((b.pos_x - mx)**2 + (b.pos_z - mz)**2)


def _alineacion_hacia_meta(b, mx, mz):
    dx = mx - b.pos_x
    dz = mz - b.pos_z
    rumbo = math.degrees(math.atan2(dx, -dz)) % 360.0
    hdg = b.heading_deg()
    desvio = abs((rumbo - hdg + 540) % 360 - 180)
    return 180.0 - desvio


class Oracle:
    def __init__(self, horizontes=None, radio_boundary=RADIO_BOUNDARY_M):
        self.horizontes = horizontes if horizontes else HORIZONTES_S
        self.radio_boundary = radio_boundary

    def _simular_receta(self, barco_base, meta_x, meta_z, receta, timeout_s):
        """Devuelve (barco, error, parametro_usado)."""
        b = copy.deepcopy(barco_base)
        parametro = None
        try:
            if receta == "corregir_rumbo":
                dx = meta_x - b.pos_x
                dz = meta_z - b.pos_z
                rumbo = math.degrees(math.atan2(dx, -dz)) % 360.0
                parametro = round(rumbo, 2)
                corregir_rumbo(b, objetivo_deg=rumbo, timeout_s=timeout_s)
            elif receta == "ir_a_punto":
                parametro = (round(meta_x, 2), round(meta_z, 2))
                ir_a_punto(b, meta_x, meta_z, tol_dist=15.0, timeout_s=timeout_s)
            elif receta == "frenar":
                parametro = 0.3
                frenar(b, timeout_s=timeout_s)
            elif receta == "terminar":
                # Accion logica terminal. No ejecuta maniobra fisica.
                dist = _distancia_a(b, meta_x, meta_z)
                if dist >= 15.0:
                    return b, "terminar_invalido", None
                # si es valido, parametro queda None
        except Exception as e:
            return b, "exception: " + str(e), None
        return b, "", parametro

    def _evaluar_una(self, barco_base, meta_x, meta_z, receta):
        dist_inicial = _distancia_a(barco_base, meta_x, meta_z)
        progresos = {}
        boundary_violation = False
        error = ""

        parametro_usado = None
        for h in self.horizontes:
            b, err, param = self._simular_receta(barco_base, meta_x, meta_z, receta, h)
            if param is not None:
                parametro_usado = param
            if err:
                error = err
                progresos[round(h, 1)] = 0.0
                continue
            dist_final = _distancia_a(b, meta_x, meta_z)
            progresos[round(h, 1)] = round(dist_inicial - dist_final, 2)
            if math.sqrt(b.pos_x**2 + b.pos_z**2) > self.radio_boundary:
                boundary_violation = True

        h_max = max(self.horizontes)
        b_max, _, _ = self._simular_receta(barco_base, meta_x, meta_z, receta, h_max)
        dist_max = _distancia_a(b_max, meta_x, meta_z)
        alineacion = _alineacion_hacia_meta(b_max, meta_x, meta_z)

        mission_complete = False
        if receta == "terminar" and error == "":
            dist_inicial = _distancia_a(barco_base, meta_x, meta_z)
            if dist_inicial < 15.0:
                mission_complete = True

        # Progreso medio temporal (integracion trapezoidal sobre horizontes)
        # Puntos: (0,0), (5,p5), (15,p15), (30,p30), (45,p45)
        horizontes_ordenados = sorted(self.horizontes)
        progreso_medio = 0.0
        if horizontes_ordenados:
            puntos = [(0.0, 0.0)]
            for h in horizontes_ordenados:
                puntos.append((h, progresos.get(round(h, 1), 0.0)))
            area = 0.0
            for i in range(len(puntos) - 1):
                t1, p1 = puntos[i]
                t2, p2 = puntos[i + 1]
                area += (t2 - t1) * (p1 + p2) / 2.0
            t_total = puntos[-1][0]
            if t_total > 0.0:
                progreso_medio = round(area / t_total, 3)

        return ResultadoReceta(
            receta=receta,
            seguro=not boundary_violation,
            progreso_por_horizonte=progresos,
            alineacion_deg=round(alineacion, 1),
            dist_final_m=round(dist_max, 2),
            pos_final=(round(b_max.pos_x, 2), round(b_max.pos_z, 2)),
            boundary_violation=boundary_violation,
            mission_complete=mission_complete,
            progreso_medio=progreso_medio,
            parametro=parametro_usado,
            error=error,
        )


    def evaluar_todas(self, barco, meta_x, meta_z):
        """Devuelve lista de ResultadoReceta ordenada (mejor primero)."""
        resultados = []
        for receta in RECETAS_DISPONIBLES:
            r = self._evaluar_una(barco, meta_x, meta_z, receta)
            resultados.append(r)
        h_max = round(max(self.horizontes), 1)
        resultados.sort(key=lambda r: (
            not r.mission_complete,
            r.boundary_violation,
            -r.progreso_medio,
            -r.alineacion_deg,
        ))
        return resultados

    def elegir(self, barco, meta_x, meta_z):
        """Devuelve el nombre de la mejor receta."""
        return self.evaluar_todas(barco, meta_x, meta_z)[0].receta

    def elegir_con_detalle(self, barco, meta_x, meta_z, near_tie_m=0.0):
        """Devuelve mejor + empates (segun near_tie) + curva por receta."""
        resultados = self.evaluar_todas(barco, meta_x, meta_z)
        mejor = resultados[0]
        h_max = round(max(self.horizontes), 1)
        progreso_mejor = mejor.progreso_medio

        empates = [mejor.receta]
        for r in resultados[1:]:
            if r.mission_complete != mejor.mission_complete:
                continue
            if r.boundary_violation != mejor.boundary_violation:
                continue
            p = r.progreso_medio
            if abs(p - progreso_mejor) <= near_tie_m:
                empates.append(r.receta)

        # Margen contra la segunda (solo cuenta si comparte estado terminal/boundary)
        margen_vs_segunda = None
        for r in resultados[1:]:
            if r.mission_complete != mejor.mission_complete:
                continue
            if r.boundary_violation != mejor.boundary_violation:
                continue
            margen_vs_segunda = round(progreso_mejor - r.progreso_medio, 3)
            break

        return {
            "mejor": mejor.receta,
            "empates": empates,
            "near_tie_m": near_tie_m,
            "margen_vs_segunda": margen_vs_segunda,
            "detalle": [
                {
                    "receta": r.receta,
                    "seguro": r.seguro,
                    "progreso_por_horizonte": r.progreso_por_horizonte,
                    "alineacion_deg": r.alineacion_deg,
                }
                for r in resultados
            ],
        }


if __name__ == "__main__":
    b = Barco()
    b.pos_x, b.pos_z = 0.0, 0.0
    b.yaw = 0.0
    meta_x, meta_z = 100.0, 100.0

    print("Estado: (0,0) hdg=0 meta=(100,100) desvio=135")
    print()
    orac = Oracle()
    detalle = orac.elegir_con_detalle(b, meta_x, meta_z, near_tie_m=1.0)
    print("Mejor:", detalle["mejor"])
    print("Empates:", detalle["empates"])
    print()
    for d in detalle["detalle"]:
        progresos = d["progreso_por_horizonte"]
        h_str = " ".join([str(k) + "s=" + str(progresos[k]) for k in sorted(progresos.keys())])
        print("  " + d["receta"] + ": seguro=" + str(d["seguro"]) + " | " + h_str)
