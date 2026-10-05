#!/usr/bin/env python3
"""
simulador_polaris.py - Simulador matematico puro de Polaris.
Replica la fisica de Godot (Jolt) sin GPU ni render.

Objetivo: entrenar a Timonel sin abrir Godot.
Interfaz: recibe comandos (timon, timon_ms, avance, avance_ms), devuelve telemetria.
"""

import math
from dataclasses import dataclass, field
from typing import Optional


# ============================================================
# CONSTANTES FISICAS (extraidas del codigo Godot)
# ============================================================

GRAVITY = 9.8
DT = 1.0 / 60.0

MASS = 3500.0
SIZE_X = 4.0
SIZE_Y = 1.0
SIZE_Z = 8.0
CENTER_OF_MASS_OFFSET = (0.0, -1.5, 0.0)

FLOAT_FORCE = 120.0
FORWARD_DRAG = 0.0134
LATERAL_DRAG = 0.15
WATER_ANGULAR_DRAG = 0.005

# Fisica avanzada (ver EXPEDIENTE/58: informe LLM Notebook)
RUDDER_EFFECT_REF_KN = 2.5      # nudos, velocidad donde el timon tiene efecto completo
PROP_WASH_FACTOR = 0.35         # efectividad del timon con throttle aplicado (chorro del helicoptero)
PROP_WALK_TORQUE = 1800.0       # N.m, torque de prop walk en reversa (helicoptero dextrogiro)
PROP_WALK_SPEED_MAX_MS = 2.5    # m/s, arriba de esto el prop walk no aplica

ROLL_STIFFNESS = 0.3
PITCH_STIFFNESS = 0.3
ROLL_DAMPING = 2.5
PITCH_DAMPING = 2.5

TIMON_TORQUE = 886.0
AVANCE_FORCE = 6000.0

PROBES_LOCAL = []
for x in (-1.5, 1.5):
    for z in (-3.0, 3.0):
        for y in (-0.5, 0.0, 0.5):
            PROBES_LOCAL.append((x, y, z))

GOAL_X = 200.0
GOAL_Z = 0.0


# ============================================================
# CLASE BARCO — Estado + integracion
# ============================================================

@dataclass
class Barco:
    # Posicion (m)
    pos_x: float = 0.0
    pos_y: float = 0.0
    pos_z: float = 0.0

    # Velocidad lineal (m/s)
    vel_x: float = 0.0
    vel_y: float = 0.0
    vel_z: float = 0.0

    # Orientacion: yaw (heading) en radianes. Por simplicidad 2D.
    # (el ABC no necesita roll/pitch — viento=0, olas=0)
    yaw: float = 0.0

    # Velocidad angular (rad/s) — solo yaw
    yaw_rate: float = 0.0

    # Comandos activos
    timon_activo: int = 0
    timon_hasta_ms: float = 0.0
    avance_activo: int = 0
    avance_hasta_ms: float = 0.0

    # Tiempo simulado (s)
    t: float = 0.0

    def heading_deg(self) -> float:
        """Heading en grados (0=norte, 90=este)."""
        # En Godot, forward = -basis.z. Con yaw=0, el barco mira hacia -Z (norte).
        # yaw positivo rota hacia la derecha (este).
        h = math.degrees(self.yaw) % 360.0
        return h

    def speed_ms(self) -> float:
        """Velocidad horizontal en m/s."""
        return math.sqrt(self.vel_x**2 + self.vel_z**2)

    def sog_kn(self) -> float:
        """Speed Over Ground en nudos."""
        return self.speed_ms() * 1.94384449

    def cog_deg(self) -> float:
        """Course Over Ground en grados. 0 si casi quieto."""
        if self.speed_ms() < 0.05:
            return 0.0
        # atan2(x, -z) — coherente con Godot
        c = math.degrees(math.atan2(self.vel_x, -self.vel_z)) % 360.0
        return c

    def dist_a_meta(self) -> float:
        return math.sqrt((self.pos_x - GOAL_X)**2 + (self.pos_z - GOAL_Z)**2)

    def aplicar_comando(self, timon: int, timon_ms: int, avance: int, avance_ms: int):
        """Registra un comando nuevo. Se aplica durante los proximos X ms."""
        self.timon_activo = timon
        self.timon_hasta_ms = self.t * 1000.0 + timon_ms if timon != 0 else 0.0
        self.avance_activo = avance
        self.avance_hasta_ms = self.t * 1000.0 + avance_ms if avance != 0 else 0.0

    def paso(self, dt: float = DT):
        """Avanza un paso de integracion."""
        # 1. Fuerza de avance (si activo)
        t_ms = self.t * 1000.0
        fx, fz = 0.0, 0.0
        if self.avance_activo != 0 and t_ms <= self.avance_hasta_ms:
            # forward = direccion segun yaw
            fx = math.sin(self.yaw) * AVANCE_FORCE * self.avance_activo
            fz = -math.cos(self.yaw) * AVANCE_FORCE * self.avance_activo
        else:
            self.avance_activo = 0

        # 2. Torque de timon (si activo) — con perdida de gobierno a baja velocidad
        torque = 0.0
        if self.timon_activo != 0 and t_ms <= self.timon_hasta_ms:
            # Efectividad por velocidad (cuadratica): a 2.5 kn efecto completo,
            # debajo decae cuadraticamente (hidrodinamica real)
            ref_ms = RUDDER_EFFECT_REF_KN / 1.94384449
            speed_factor = min(1.0, (self.speed_ms() / ref_ms) ** 2)
            # Prop wash: si hay throttle aplicado, el chorro del helicoptero
            # le da autoridad al timon incluso a velocidad cero
            prop_wash_factor = PROP_WASH_FACTOR if self.avance_activo != 0 else 0.0
            # Tomar el mayor de los dos factores
            efectividad = max(speed_factor, prop_wash_factor)
            torque = TIMON_TORQUE * self.timon_activo * efectividad
        else:
            self.timon_activo = 0

        # 2b. Prop walk: en reversa a baja velocidad, la popa se va a babor
        # (helicoptero dextrogiro), lo que hace girar la proa a estribor
        if self.avance_activo < 0 and self.speed_ms() < PROP_WALK_SPEED_MAX_MS:
            walk_factor = max(0.0, 1.0 - self.speed_ms() / PROP_WALK_SPEED_MAX_MS)
            torque += PROP_WALK_TORQUE * walk_factor * abs(self.avance_activo)

        # 3. Integrar velocidad lineal (F = m*a -> a = F/m)
        ax = fx / MASS
        az = fz / MASS
        self.vel_x += ax * dt
        self.vel_z += az * dt

        # 4. Drag hidrodinamico (descomponer forward/lateral)
        # forward en world segun yaw
        fwd_x = math.sin(self.yaw)
        fwd_z = -math.cos(self.yaw)
        # Componente forward
        v_fwd = self.vel_x * fwd_x + self.vel_z * fwd_z
        # Componente lateral (perpendicular)
        lat_x = -fwd_z
        lat_z = fwd_x
        v_lat = self.vel_x * lat_x + self.vel_z * lat_z
        # Amortiguar
        v_fwd *= (1.0 - FORWARD_DRAG)
        v_lat *= (1.0 - LATERAL_DRAG)
        # Recomponer
        self.vel_x = v_fwd * fwd_x + v_lat * lat_x
        self.vel_z = v_fwd * fwd_z + v_lat * lat_z

        # 5. Integrar torque angular
        # Inercia (aprox. de caja rectangular respecto a Y)
        I_y = MASS * (SIZE_X**2 + SIZE_Z**2) / 12.0
        alpha = torque / I_y
        self.yaw_rate += alpha * dt
        self.yaw_rate *= (1.0 - WATER_ANGULAR_DRAG)

        # 6. Integrar posicion y yaw
        self.pos_x += self.vel_x * dt
        self.pos_z += self.vel_z * dt
        self.yaw += self.yaw_rate * dt

        # 7. Tiempo
        self.t += dt


# ============================================================
# INTERFAZ — Leer comandos, escribir telemetria
# ============================================================

import os
import time
import json
from pathlib import Path

GODOT_DIR = Path.home() / ".local/share/godot/app_userdata/interfaz/timonel"
TELEMETRIA = GODOT_DIR / "telemetria.jsonl"
COMANDOS = GODOT_DIR / "comandos.jsonl"

class Runner:
    """Loop principal: lee comandos de comandos.jsonl, avanza fisica, escribe telemetria."""
    def __init__(self, barco: Optional[Barco] = None):
        self.barco = barco or Barco()
        GODOT_DIR.mkdir(parents=True, exist_ok=True)
        # Limpiar archivos
        TELEMETRIA.write_text("")
        COMANDOS.write_text("")
        self._telemetria_fh = open(TELEMETRIA, "a")
        self._comandos_fh = open(COMANDOS, "a")
        self._ultimo_t_leido = 0.0

    def _leer_comando_nuevo(self) -> Optional[dict]:
        """Lee ultima linea de comandos.jsonl y devuelve si es nueva."""
        if not COMANDOS.exists():
            return None
        try:
            with open(COMANDOS) as f:
                lineas = f.readlines()
        except Exception:
            return None
        if not lineas:
            return None
        ultima = lineas[-1].strip()
        if not ultima:
            return None
        try:
            c = json.loads(ultima)
        except json.JSONDecodeError:
            return None
        t_c = c.get("t", 0) / 1000.0
        if t_c <= self._ultimo_t_leido:
            return None
        self._ultimo_t_leido = t_c
        return c

    def _escribir_telemetria(self):
        b = self.barco
        linea = {
            "t": int(b.t * 1000),
            "pos_x": round(b.pos_x, 3),
            "pos_y": round(b.pos_y, 3),
            "pos_z": round(b.pos_z, 3),
            "sog_kn": round(b.sog_kn(), 3),
            "cog_deg": round(b.cog_deg(), 2),
            "hdg_deg": round(b.heading_deg(), 2),
            "aws_kn": 0.0,
            "awa_deg": 0.0,
            "dist_a_meta": round(b.dist_a_meta(), 2),
            "progreso": 0.0,
            "roll_deg": 0.0,
            "pitch_deg": 0.0,
            "yaw_deg": round(math.degrees(b.yaw), 2),
        }
        self._telemetria_fh.write(json.dumps(linea) + "\n")
        self._telemetria_fh.flush()

    def correr(self, duracion_s: float = 60.0, telemetria_hz: float = 1.0):
        """Corre el simulador durante duracion_s segundos.
        telemetria_hz: cada cuantos Hz se escribe telemetria (1 Hz = 1 vez por segundo).
        Fisica a 60 Hz, telemetria a 1 Hz."""
        pasos_por_telemetria = int(1.0 / (DT * telemetria_hz))
        paso_actual = 0
        t_inicio = time.time()
        while self.barco.t < duracion_s:
            # 1. Leer comando nuevo (si hay)
            c = self._leer_comando_nuevo()
            if c:
                self.barco.aplicar_comando(
                    timon=int(c.get("timon", 0)),
                    timon_ms=int(c.get("timon_ms", 0)),
                    avance=int(c.get("avance", 0)),
                    avance_ms=int(c.get("avance_ms", 0)),
                )
            # 2. Avanzar fisica
            self.barco.paso()
            paso_actual += 1
            # 3. Escribir telemetria cada N pasos
            if paso_actual >= pasos_por_telemetria:
                self._escribir_telemetria()
                paso_actual = 0

    def cerrar(self):
        self._telemetria_fh.close()
        self._comandos_fh.close()


# ============================================================
# MAIN — Para prueba rapida
# ============================================================

if __name__ == "__main__":
    import sys
    dur = float(sys.argv[1]) if len(sys.argv) > 1 else 60.0
    print(f"[sim] arrancando. Duracion: {dur}s")
    runner = Runner()
    try:
        runner.correr(duracion_s=dur)
    except KeyboardInterrupt:
        print("[sim] interrumpido")
    finally:
        runner.cerrar()
        print(f"[sim] listo. t final: {runner.barco.t:.1f}s")
        print(f"[sim] pos final: ({runner.barco.pos_x:.1f}, {runner.barco.pos_z:.1f})")
        print(f"[sim] dist a meta: {runner.barco.dist_a_meta():.1f} m")
