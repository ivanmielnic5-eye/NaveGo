#!/usr/bin/env python3
"""
timonel_python.py - Agente que pilota Polaris en el simulador Python.
Arquitectura: LLM decide QUE RECETA usar, no los comandos de bajo nivel.
"""

import argparse
import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from simulador_polaris import Barco, DT, GOAL_X, GOAL_Z
from recetas_navegacion import corregir_rumbo, ir_a_punto, frenar, delta_angulo


@dataclass
class Paso:
    t: float
    pos_x: float
    pos_z: float
    hdg: float
    sog: float
    dist_meta: float
    decision: str
    argumento: str
    exito: bool
    detalle: dict


@dataclass
class Corrida:
    fecha: str
    meta_x: float
    meta_z: float
    pos_inicial: tuple
    hdg_inicial: float
    pasos: list
    resultado: str
    dist_final: float
    t_total: float
    num_pasos: int
    modelo_llm: str


def distancia_a(barco: Barco, mx: float, mz: float) -> float:
    return math.sqrt((barco.pos_x - mx) ** 2 + (barco.pos_z - mz) ** 2)


def angulo_hacia(barco: Barco, mx: float, mz: float) -> float:
    dx = mx - barco.pos_x
    dz = mz - barco.pos_z
    return math.degrees(math.atan2(dx, -dz)) % 360.0


def guardar_corrida(corrida: Corrida, dir_salida: Path):
    dir_salida.mkdir(parents=True, exist_ok=True)
    nombre = f"corrida_{corrida.fecha.replace(':', '-').replace(' ', '_')}.json"
    ruta = dir_salida / nombre
    with ruta.open("w", encoding="utf-8") as f:
        json.dump(asdict(corrida), f, indent=2, ensure_ascii=False)
    return ruta


class AgenteTimonel:
    """Agente que decide maniobras y las ejecuta en el simulador."""

    def __init__(self, meta_x: float, meta_z: float,
                 timeout_s: float = 300.0, usar_llm: bool = False):
        self.meta_x = meta_x
        self.meta_z = meta_z
        self.timeout_s = timeout_s
        self.usar_llm = usar_llm
        self.barco = Barco()
        self.pasos: list = []
        self.t_inicio = 0.0
        self.llm_fallos = 0

    def _registrar_paso(self, decision: str, argumento: str, exito: bool, detalle: dict):
        paso = Paso(
            t=round(self.barco.t, 2),
            pos_x=round(self.barco.pos_x, 2),
            pos_z=round(self.barco.pos_z, 2),
            hdg=round(self.barco.heading_deg(), 1),
            sog=round(self.barco.sog_kn(), 2),
            dist_meta=round(distancia_a(self.barco, self.meta_x, self.meta_z), 1),
            decision=decision,
            argumento=argumento,
            exito=exito,
            detalle=detalle,
        )
        self.pasos.append(paso)

    def _decidir_por_reglas(self) -> tuple:
        """Decision por reglas simples. Fallback y baseline."""
        dist = distancia_a(self.barco, self.meta_x, self.meta_z)
        if dist < 15.0:
            return ("terminar", "llegado")
        obj_deg = angulo_hacia(self.barco, self.meta_x, self.meta_z)
        hdg = self.barco.heading_deg()
        delta = abs(delta_angulo(hdg, obj_deg))
        if delta < 20.0:
            return ("ir_a_punto", f"meta=({self.meta_x},{self.meta_z})")
        else:
            return ("corregir_rumbo", f"objetivo={obj_deg:.0f}")

    def _decidir_con_llm(self) -> tuple:
        """Consulta a Qwen. Si falla, cae en reglas simples."""
        try:
            from agente_llm import decidir_con_qwen
            decision = decidir_con_qwen(self.meta_x, self.meta_z, self.barco)
        except Exception as e:
            self.llm_fallos += 1
            return self._decidir_por_reglas()

        if "_error" in decision:
            self.llm_fallos += 1
            return self._decidir_por_reglas()

        accion = decision.get("accion")
        parametro = decision.get("parametro")

        if accion == "corregir_rumbo":
            try:
                obj = float(parametro)
                return ("corregir_rumbo", f"objetivo={obj:.0f}")
            except Exception:
                self.llm_fallos += 1
                return self._decidir_por_reglas()
        elif accion == "ir_a_punto":
            try:
                mx, mz = parametro
                return ("ir_a_punto", f"meta=({mx},{mz})")
            except Exception:
                self.llm_fallos += 1
                return self._decidir_por_reglas()
        elif accion == "frenar":
            return ("frenar", "ordenado")
        elif accion == "terminar":
            return ("terminar", "llegado")
        else:
            self.llm_fallos += 1
            return self._decidir_por_reglas()

    def _decidir(self) -> tuple:
        """Decision del agente: LLM si esta activo, si no reglas simples."""
        if self.usar_llm:
            return self._decidir_con_llm()
        return self._decidir_por_reglas()

    def correr(self, verbose: bool = False) -> Corrida:
        self.t_inicio = self.barco.t
        pos_inicial = (round(self.barco.pos_x, 2), round(self.barco.pos_z, 2))
        hdg_inicial = round(self.barco.heading_deg(), 1)

        if verbose:
            print(f"[agente] Meta: ({self.meta_x}, {self.meta_z}) | inicio: {pos_inicial} hdg={hdg_inicial}")

        resultado = "TIMEOUT"
        paso_num = 0

        while self.barco.t - self.t_inicio < self.timeout_s:
            dist = distancia_a(self.barco, self.meta_x, self.meta_z)
            if dist < 15.0:
                resultado = "LLEGO"
                break

            decision, argumento = self._decidir()
            paso_num += 1

            if decision == "corregir_rumbo":
                obj_deg = float(argumento.split("=")[1])
                exito, detalle = corregir_rumbo(self.barco, objetivo_deg=obj_deg, timeout_s=60.0)
            elif decision == "ir_a_punto":
                exito, detalle = ir_a_punto(self.barco, self.meta_x, self.meta_z, tol_dist=15.0, timeout_s=90.0)
            elif decision == "frenar":
                exito, detalle = frenar(self.barco, timeout_s=30.0)
            elif decision == "terminar":
                resultado = "LLEGO"
                break
            else:
                exito, detalle = False, {"error": "decision desconocida"}

            self._registrar_paso(decision, argumento, exito, detalle)

            if verbose:
                print(f"[agente] paso {paso_num}: {decision}({argumento}) exito={exito} dist={dist:.1f}m t={self.barco.t:.1f}s")

        dist_final = distancia_a(self.barco, self.meta_x, self.meta_z)
        corrida = Corrida(
            fecha=datetime.now().isoformat(timespec="seconds"),
            meta_x=self.meta_x,
            meta_z=self.meta_z,
            pos_inicial=pos_inicial,
            hdg_inicial=hdg_inicial,
            pasos=[asdict(p) for p in self.pasos],
            resultado=resultado,
            dist_final=round(dist_final, 1),
            t_total=round(self.barco.t - self.t_inicio, 1),
            num_pasos=len(self.pasos),
            modelo_llm="qwen1.5b" if self.usar_llm else "reglas",
        )
        if self.usar_llm:
            print(f"[agente] fallos de LLM: {self.llm_fallos}")
        return corrida


def main():
    parser = argparse.ArgumentParser(description="Timonel Python (agente en simulador)")
    parser.add_argument("--meta-x", type=float, default=200.0)
    parser.add_argument("--meta-z", type=float, default=0.0)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--guardar", action="store_true")
    parser.add_argument("--llm", action="store_true",
                        help="Usar Qwen 1.5B para decidir. Si no, reglas simples.")
    args = parser.parse_args()

    agente = AgenteTimonel(
        meta_x=args.meta_x, meta_z=args.meta_z,
        timeout_s=args.timeout,
        usar_llm=args.llm,
    )
    corrida = agente.correr(verbose=args.verbose)

    print()
    print("=" * 60)
    print(" RESULTADO DE LA CORRIDA")
    print("=" * 60)
    print(f"  Resultado:    {corrida.resultado}")
    print(f"  Dist final:   {corrida.dist_final} m")
    print(f"  Tiempo total: {corrida.t_total} s")
    print(f"  Pasos:        {corrida.num_pasos}")
    if corrida.pasos:
        print()
        print("  Historial:")
        for p in corrida.pasos:
            print(f"    t={p['t']:>6.1f}s | {p['decision']:>16s} | {p['argumento']:>25s} | exito={p['exito']}")

    if args.guardar:
        ruta = guardar_corrida(corrida, Path.home() / "navego_recuperado" / "timonel" / "corridas")
        print()
        print(f"  Guardada en: {ruta}")


if __name__ == "__main__":
    main()
