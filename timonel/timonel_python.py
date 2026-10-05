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

    def __init__(self, meta_x: float = None, meta_z: float = None,
                 metas: list = None,
                 timeout_s: float = 300.0, usar_llm: bool = False,
                 conn=None, max_pasos: int = 15):
        # Compatibilidad: acepta meta_x/meta_z O metas (lista)
        if metas is not None:
            self.metas = list(metas)
        elif meta_x is not None and meta_z is not None:
            self.metas = [(meta_x, meta_z)]
        else:
            raise ValueError("Hay que pasar meta_x/meta_z o metas")
        self.meta_x = self.metas[0][0]
        self.meta_z = self.metas[0][1]
        self.timeout_s = timeout_s
        self.usar_llm = usar_llm
        self.conn = conn
        self.max_pasos = max_pasos
        self.barco = Barco()
        self.pasos: list = []
        self.t_inicio = 0.0
        self.llm_fallos = 0
        self.terminar_prematuros = 0
        self.metas_alcanzadas = 0
        self.tiempo_congelado = 0
        self.estados_evaluados = []

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
            decision = decidir_con_qwen(self.meta_x, self.meta_z, self.barco, conn=self.conn)
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
            # Meta actual = primera de la lista
            self.meta_x, self.meta_z = self.metas[0]
            dist = distancia_a(self.barco, self.meta_x, self.meta_z)

            if dist < 15.0:
                # Llego a la meta actual. Sacarla y seguir.
                self.metas.pop(0)
                self.metas_alcanzadas += 1
                if not self.metas:
                    # No hay mas metas: mision cumplida.
                    resultado = "LLEGO"
                    break
                # Hay mas metas: continuar sin cortar
                continue

            if paso_num >= self.max_pasos:
                resultado = "FRACASO"
                break

            decision, argumento = self._decidir()
            paso_num += 1
            t_al_inicio_paso = self.barco.t

            # Instrumentacion: guardar estado + decision + contexto
            self.estados_evaluados.append({
                "paso_num": paso_num,
                "t": round(self.barco.t, 2),
                "pos_x": round(self.barco.pos_x, 3),
                "pos_z": round(self.barco.pos_z, 3),
                "hdg": round(self.barco.heading_deg(), 2),
                "sog": round(self.barco.sog_kn(), 2),
                "meta_x": self.meta_x,
                "meta_z": self.meta_z,
                "dist_meta": round(dist, 2),
                "viento_kn": round(self.barco.viento_intensidad_kn, 1),
                "viento_dir": round(self.barco.viento_direccion_deg, 1),
                "decision": decision,
                "argumento": argumento,
            })

            if decision == "corregir_rumbo":
                obj_deg = float(argumento.split("=")[1])
                exito, detalle = corregir_rumbo(self.barco, objetivo_deg=obj_deg, timeout_s=60.0)
            elif decision == "ir_a_punto":
                exito, detalle = ir_a_punto(self.barco, self.meta_x, self.meta_z, tol_dist=15.0, timeout_s=90.0)
            elif decision == "frenar":
                exito, detalle = frenar(self.barco, timeout_s=30.0)
            elif decision == "terminar":
                # NO confiar en el LLM. Verificar la distancia real.
                if dist < 15.0:
                    resultado = "LLEGO"
                    break
                else:
                    # El LLM quiere terminar pero no llego. Ignorar y ejecutar
                    # ir_a_punto como fallback (asi el barco AVANZA de verdad).
                    self.terminar_prematuros += 1
                    if self.terminar_prematuros >= 5:
                        resultado = "TIMEOUT"
                        break
                    # Fallback: ejecutar ir_a_punto hacia la meta
                    exito, detalle = ir_a_punto(
                        self.barco, self.meta_x, self.meta_z,
                        tol_dist=15.0, timeout_s=60.0
                    )
                    # Registrar como si hubiera decidido ir_a_punto
                    decision = "ir_a_punto_fallback"
                    argumento = f"meta=({self.meta_x},{self.meta_z})"
            else:
                exito, detalle = False, {"error": "decision desconocida"}

            # Resetear contador si ejecutamos una accion real (no terminar_prematuro)
            if decision != "terminar":
                self.terminar_prematuros = 0

            # Detectar receta que no avanza tiempo (loop atascado)
            t_antes = t_al_inicio_paso
            if self.barco.t <= t_antes + 0.1:
                self.tiempo_congelado += 1
                if self.tiempo_congelado >= 3:
                    # Fallback: forzar ir_a_punto hacia meta actual
                    ir_a_punto(self.barco, self.meta_x, self.meta_z,
                               tol_dist=15.0, timeout_s=60.0)
                    self.tiempo_congelado = 0
                    if self.barco.t <= t_antes + 0.1:
                        # Ni ir_a_punto avanzó: cortar
                        resultado = "FRACASO"
                        self._registrar_paso(decision, argumento, False,
                                             {"error": "tiempo_congelado"})
                        break
            else:
                self.tiempo_congelado = 0

            self._registrar_paso(decision, argumento, exito, detalle)

            if verbose:
                print(f"[agente] paso {paso_num}: {decision}({argumento}) exito={exito} dist={dist:.1f}m t={self.barco.t:.1f}s")

        dist_final = distancia_a(self.barco, self.meta_x, self.meta_z)

        # Si terminamos por timeout pero el barco esta en rango de llegada,
        # marcarlo como LLEGO (el loop puede haber salido sin chequear).
        if resultado == "TIMEOUT" and dist_final < 15.0:
            resultado = "LLEGO"

        corrida = Corrida(
            fecha=datetime.now().isoformat(timespec="seconds"),
            meta_x=self.metas[-1][0] if self.metas else 0.0,
            meta_z=self.metas[-1][1] if self.metas else 0.0,
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
        if self.metas_alcanzadas > 0:
            print(f"[agente] metas alcanzadas: {self.metas_alcanzadas}")
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
    parser.add_argument("--memoria", action="store_true",
                        help="Consultar la memoria SQLite para inyectar experiencias.")
    args = parser.parse_args()

    conn = None
    if args.memoria:
        try:
            from memoria import conectar
            conn = conectar()
            print("[main] memoria conectada")
        except Exception as e:
            print(f"[main] no se pudo conectar a memoria: {e}")

    agente = AgenteTimonel(
        meta_x=args.meta_x, meta_z=args.meta_z,
        timeout_s=args.timeout,
        usar_llm=args.llm,
        conn=conn,
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
