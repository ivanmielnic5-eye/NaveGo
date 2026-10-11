#!/usr/bin/env python3
"""controlador_pid.py - Controlador PID (Proporcional-Integral-Derivativo)
para rumbo del velero.

Salida CONTINUA en [-1.0, 1.0]. Reemplaza las "recetas" open-loop.

Arquitectura en cascada (Claude + Notebook LLM):
- Inner loop (aqui): PID de rumbo a 60 Hz.
- Outer loop (futuro): el LLM decide el rumbo.

Convencion de signos:
- error = rumbo_objetivo - heading, signed en [-180, 180].
- error > 0 -> girar a estribor -> timon > 0.
- error < 0 -> girar a babor -> timon < 0.

Referencia: EXPEDIENTE/89 seccion 10.bis y Anexo A.
"""

import math
from simulador_polaris import Barco, DT


def delta_angulo(actual_deg: float, objetivo_deg: float) -> float:
    """Diferencia angular signed. Rango [-180, 180]."""
    return (objetivo_deg - actual_deg + 540.0) % 360.0 - 180.0


def rumbo_a_meta(b: Barco, meta_x: float, meta_z: float) -> float:
    """Rumbo en grados (0=norte) desde la posicion actual hacia la meta."""
    dx = meta_x - b.pos_x
    dz = meta_z - b.pos_z
    return math.degrees(math.atan2(dx, -dz)) % 360.0


class PIDRumbo:
    """Control PID continuo para mantener rumbo.

    Salida: float en [-1.0, 1.0] que se pasa a aplicar_comando.
    """

    def __init__(self, Kp=0.10, Ki=0.0, Kd=0.25,
                 integral_limit=20.0, tolerancia=1.0):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.integral_limit = integral_limit
        self.tolerancia = tolerancia
        self._integral = 0.0

    def reset(self):
        self._integral = 0.0

    def paso(self, b: Barco, rumbo_objetivo: float, dt: float = DT) -> float:
        hdg = b.heading_deg()
        error = delta_angulo(hdg, rumbo_objetivo)

        if abs(error) < self.tolerancia:
            return 0.0

        # Termino proporcional
        P = self.Kp * error

        # Termino integral (con anti-windup)
        self._integral += error * dt
        if self._integral > self.integral_limit:
            self._integral = self.integral_limit
        elif self._integral < -self.integral_limit:
            self._integral = -self.integral_limit
        I = self.Ki * self._integral

        # Termino derivativo: la tasa de giro actual frena la salida.
        yaw_rate_deg_s = math.degrees(b.yaw_rate)
        D = self.Kd * yaw_rate_deg_s

        u = P + I - D

        # Saturacion
        if u > 1.0:
            u = 1.0
        elif u < -1.0:
            u = -1.0

        return u
