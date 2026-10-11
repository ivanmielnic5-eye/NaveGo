#!/usr/bin/env python3
"""entrenador_v2.py - Entrenador con continuacion comun.

Corrige el bug del Entrenador v1:
- v1: cada receta corria hasta que TERMINABA o hasta timeout.
  Duraciones distintas -> comparacion injusta.
- v2: cada accion corre TODO el horizonte. Comparacion justa.

Usa acciones.py (interfaz de alto nivel con setpoints).

Referencia: EXPEDIENTE/89.
"""

import copy
import math

from simulador_polaris import Barco, DT
from acciones import (
    accion_rumbo,
    accion_ir_a,
    accion_frenar,
    accion_terminar,
)
from controlador_pid import rumbo_a_meta


HORIZONTES_DEFAULT = [5.0, 15.0, 30.0, 45.0]
RADIO_BOUNDARY_DEFAULT = 500.0


def _distancia_a(b: Barco, mx: float, mz: float) -> float:
    return math.sqrt((b.pos_x - mx)**2 + (b.pos_z - mz)**2)


def _alineacion_hacia_meta(b: Barco, mx: float, mz: float) -> float:
    """Alineacion: 180 = alineado perfecto, 0 = mirando al lado opuesto."""
    dx = mx - b.pos_x
    dz = mz - b.pos_z
    rumbo = math.degrees(math.atan2(dx, -dz)) % 360.0
    hdg = b.heading_deg()
    desvio = abs((rumbo - hdg + 540) % 360 - 180)
    return 180.0 - desvio


class ResultadoAccion:
    """Resultado de evaluar una accion."""

    def __init__(self, accion, seguro, progreso_por_horizonte,
                 alineacion_deg, dist_final_m, pos_final,
                 boundary_violation, mission_complete, progreso_medio,
                 dist_al_origen_final=0.0, parametro=None, error=""):
        self.accion = accion
        self.seguro = seguro
        self.progreso_por_horizonte = progreso_por_horizonte
        self.alineacion_deg = alineacion_deg
        self.dist_final_m = dist_final_m
        self.pos_final = pos_final
        self.boundary_violation = boundary_violation
        self.mission_complete = mission_complete
        self.progreso_medio = progreso_medio
        self.dist_al_origen_final = dist_al_origen_final
        self.parametro = parametro
        self.error = error


class Entrenador:
    """Entrenador v2. Todas las acciones corren el horizonte completo."""

    def __init__(self, horizontes=None, radio_boundary=RADIO_BOUNDARY_DEFAULT):
        self.horizontes = horizontes if horizontes else HORIZONTES_DEFAULT
        self.radio_boundary = radio_boundary
        self.acciones_disponibles = ["rumbo", "ir_a", "frenar", "terminar"]

    def _evaluar_accion(self, barco_base, meta_x, meta_z, accion):
        """Evalua una accion sobre TODOS los horizontes."""
        dist_inicial = _distancia_a(barco_base, meta_x, meta_z)
        progresos = {}
        boundary_violation = False
        error = ""
        parametro_usado = None

        for h in self.horizontes:
            b = copy.deepcopy(barco_base)
            try:
                if accion == "rumbo":
                    theta = rumbo_a_meta(b, meta_x, meta_z)
                    parametro_usado = round(theta, 2)
                    _, det = accion_rumbo(b, theta, h)
                elif accion == "ir_a":
                    parametro_usado = (round(meta_x, 2), round(meta_z, 2))
                    _, det = accion_ir_a(b, meta_x, meta_z, h)
                elif accion == "frenar":
                    parametro_usado = 0.3
                    _, det = accion_frenar(b, h)
                elif accion == "terminar":
                    parametro_usado = None
                    _, det = accion_terminar(b, meta_x, meta_z, h)
                else:
                    error = "accion_desconocida"
                    progresos[round(h, 1)] = 0.0
                    continue
            except Exception as e:
                error = "exception: " + str(e)
                progresos[round(h, 1)] = 0.0
                continue

            dist_final = _distancia_a(b, meta_x, meta_z)
            progresos[round(h, 1)] = round(dist_inicial - dist_final, 2)
            if math.sqrt(b.pos_x**2 + b.pos_z**2) > self.radio_boundary:
                boundary_violation = True

        # Estado al horizonte maximo
        h_max = max(self.horizontes)
        b_max = copy.deepcopy(barco_base)
        try:
            if accion == "rumbo":
                theta = rumbo_a_meta(b_max, meta_x, meta_z)
                accion_rumbo(b_max, theta, h_max)
            elif accion == "ir_a":
                accion_ir_a(b_max, meta_x, meta_z, h_max)
            elif accion == "frenar":
                accion_frenar(b_max, h_max)
            elif accion == "terminar":
                accion_terminar(b_max, meta_x, meta_z, h_max)
        except Exception:
            pass

        dist_max = _distancia_a(b_max, meta_x, meta_z)
        alineacion = _alineacion_hacia_meta(b_max, meta_x, meta_z)
        dist_al_origen_final = math.sqrt(b_max.pos_x**2 + b_max.pos_z**2)

        # Mission complete
        mission_complete = False
        if accion == "terminar" and error == "":
            if dist_inicial < 15.0:
                mission_complete = True

        # Progreso medio temporal (integracion trapezoidal)
        horizontes_ordenados = sorted(self.horizontes)
        puntos = [(0.0, 0.0)]
        for h in horizontes_ordenados:
            puntos.append((h, progresos.get(round(h, 1), 0.0)))
        area = 0.0
        for i in range(len(puntos) - 1):
            t1, p1 = puntos[i]
            t2, p2 = puntos[i + 1]
            area += (t2 - t1) * (p1 + p2) / 2.0
        t_total = puntos[-1][0]
        progreso_medio = round(area / t_total, 3) if t_total > 0 else 0.0

        return ResultadoAccion(
            accion=accion,
            seguro=not boundary_violation,
            progreso_por_horizonte=progresos,
            alineacion_deg=round(alineacion, 1),
            dist_final_m=round(dist_max, 2),
            pos_final=(round(b_max.pos_x, 2), round(b_max.pos_z, 2)),
            boundary_violation=boundary_violation,
            mission_complete=mission_complete,
            progreso_medio=progreso_medio,
            dist_al_origen_final=round(dist_al_origen_final, 2),
            parametro=parametro_usado,
            error=error,
        )

    def _peligro_inminente(self, barco, margen_m=50.0):
        """Determina si hay peligro inminente de salir del limite.

        Criterio:
        - El barco esta a menos de margen_m del radio de boundary.
        - Su velocidad tiene componente hacia afuera.

        Returns:
            True si hay peligro inminente.
            False si no.
        """
        dist_al_origen = math.sqrt(barco.pos_x**2 + barco.pos_z**2)
        margen = self.radio_boundary - dist_al_origen

        if margen > margen_m:
            return False  # Lejos del limite, no hay peligro

        # Esta cerca del limite. Ver si va hacia afuera.
        if dist_al_origen < 1e-6:
            return False  # En el origen, no se puede calcular direccion

        # Vector radial (hacia afuera)
        radial_x = barco.pos_x / dist_al_origen
        radial_z = barco.pos_z / dist_al_origen

        # Componente radial de la velocidad
        vel_radial = barco.vel_x * radial_x + barco.vel_z * radial_z

        # Si va hacia afuera con velocidad, es peligro inminente
        return vel_radial > 0.5  # > 0.5 m/s hacia afuera

    def evaluar_todas(self, barco, meta_x, meta_z):
        """Evalua las 4 acciones con el nuevo orden jerarquico.

        Orden:
        1. Si hay peligro inminente: gana la que aleja del limite.
        2. Si no: ranking por (mission_complete, progreso, alineacion,
           boundary como desempate).

        NO congela la accion si todas violan boundary.
        """
        resultados = []
        for accion in self.acciones_disponibles:
            r = self._evaluar_accion(barco, meta_x, meta_z, accion)
            resultados.append(r)

        # Detectar peligro inminente
        peligro = self._peligro_inminente(barco)

        if peligro:
            # La accion que MAS aleja del limite gana.
            # Metrica: mayor margen al final (dist_al_origen_final mas chica).
            # Si dos acciones terminan igual, desempatar por progreso.
            resultados.sort(key=lambda r: (
                r.dist_al_origen_final,   # menor dist_al_origen = mas seguro
                not r.mission_complete,
                -r.progreso_medio,
            ))
        else:
            # Ranking normal. boundary_violation como desempate.
            resultados.sort(key=lambda r: (
                not r.mission_complete,
                -r.progreso_medio,
                -r.alineacion_deg,
                r.boundary_violation,  # desempate al final
            ))
        return resultados

    def elegir(self, barco, meta_x, meta_z):
        """Devuelve el nombre de la mejor accion."""
        return self.evaluar_todas(barco, meta_x, meta_z)[0].accion

    def elegir_con_detalle(self, barco, meta_x, meta_z, near_tie_m=1.0):
        """Devuelve mejor + empates + margen."""
        resultados = self.evaluar_todas(barco, meta_x, meta_z)
        mejor = resultados[0]
        progreso_mejor = mejor.progreso_medio

        empates = [mejor.accion]
        for r in resultados[1:]:
            if r.mission_complete != mejor.mission_complete:
                continue
            if r.boundary_violation != mejor.boundary_violation:
                continue
            if abs(r.progreso_medio - progreso_mejor) <= near_tie_m:
                empates.append(r.accion)

        margen_vs_segunda = None
        for r in resultados[1:]:
            if r.mission_complete != mejor.mission_complete:
                continue
            if r.boundary_violation != mejor.boundary_violation:
                continue
            margen_vs_segunda = round(progreso_mejor - r.progreso_medio, 3)
            break

        return {
            "mejor": mejor.accion,
            "empates": empates,
            "near_tie_m": near_tie_m,
            "margen_vs_segunda": margen_vs_segunda,
            "detalle": [
                {
                    "accion": r.accion,
                    "seguro": r.seguro,
                    "progreso_medio": r.progreso_medio,
                    "progreso_por_horizonte": r.progreso_por_horizonte,
                    "alineacion_deg": r.alineacion_deg,
                    "mission_complete": r.mission_complete,
                }
                for r in resultados
            ],
        }
