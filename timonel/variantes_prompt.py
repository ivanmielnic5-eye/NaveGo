#!/usr/bin/env python3
"""variantes_prompt.py - Las 4 variantes de prompt para comparar.

VA: prompt actual (contrato pobre).
VB: contrato corregido (proposito + estado + acciones + admisibles + consecuencias).
VC: VB + enfasis visual.
VD: VB + few-shot con 4 ejemplos.

Referencia: EXPEDIENTE/77 y EXPEDIENTE/78.
"""
import math


def _desvio(rumbo_meta, hdg):
    return abs((rumbo_meta - hdg + 540) % 360 - 180)


def _fase(dist):
    return "TERMINAL" if dist < 15.0 else "NAVEGANDO"


def prompt_VA(meta_x, meta_z, pos_x, pos_z, hdg, sog, dist, rumbo_meta, viento_kn=0.0, viento_dir=0.0):
    """Contrato pobre. El actual."""
    desv = _desvio(rumbo_meta, hdg)
    linea_viento = f"- Viento: {viento_kn:.1f} nudos desde {viento_dir:.0f} grados\n" if viento_kn > 0 else ""
    return f"""Sos el timonel de un velero. Mision: llegar a la meta.

ESTADO ACTUAL:
- Posicion: ({pos_x:.1f}, {pos_z:.1f})
- Meta: ({meta_x:.1f}, {meta_z:.1f})
- Distancia a meta: {dist:.1f} metros
- Heading (proa): {hdg:.1f} grados
- Rumbo hacia la meta: {rumbo_meta:.1f} grados
- Desvio actual: {desv:.1f} grados
- Velocidad: {sog:.2f} nudos
{linea_viento}
ACCIONES DISPONIBLES:
- corregir_rumbo: gira la proa a un angulo absoluto (0-360).
- ir_a_punto: navega hacia coordenadas [x, z].
- frenar: reduce velocidad a ~0.3 nudos.
- terminar: declara mision cumplida (solo si dist < 15m).

TAREA:
Analiza el estado y elegi la accion que mejor contribuya al objetivo.

Responde UNICAMENTE con JSON:
{{"accion": "<accion>", "parametro": <valor o null>}}
"""


def prompt_VB(meta_x, meta_z, pos_x, pos_z, hdg, sog, dist, rumbo_meta, viento_kn=0.0, viento_dir=0.0):
    """Contrato corregido: proposito + estado + acciones + admisibles + consecuencias."""
    desv = _desvio(rumbo_meta, hdg)
    fase = _fase(dist)
    linea_viento = f"- Viento: {viento_kn:.1f} nudos desde {viento_dir:.0f} grados\n" if viento_kn > 0 else ""

    # Acciones admisibles segun estado
    if dist < 15.0:
        admisibles = "corregir_rumbo, ir_a_punto, frenar, terminar"
        nota_adm = "(todas las acciones son admisibles en esta fase)"
    else:
        admisibles = "corregir_rumbo, ir_a_punto, frenar"
        nota_adm = "(terminar NO es admisible: el barco aun no esta en el radio de llegada)"

    return f"""Sos el timonel de un velero autonomo. Tu objetivo es completar la mision de navegacion.

=== PROPOSITO ===
Llevar el barco hasta la meta de forma segura y eficiente.
La mision se completa cuando el barco esta dentro de 15 metros de la meta.

=== ESTADO ACTUAL ===
- Posicion: ({pos_x:.1f}, {pos_z:.1f})
- Meta: ({meta_x:.1f}, {meta_z:.1f})
- Distancia a meta: {dist:.1f} metros
- Heading (proa): {hdg:.1f} grados (0=norte, 90=este)
- Rumbo hacia la meta: {rumbo_meta:.1f} grados
- Desvio actual: {desv:.1f} grados
- Velocidad: {sog:.2f} nudos
{linea_viento}
=== ACCIONES DISPONIBLES ===

1) corregir_rumbo
   Que hace: gira la proa a un angulo absoluto entre 0 y 360.
   Consecuencia: el barco reorienta pero no avanza mientras gira.
   Parametro: angulo en grados.

2) ir_a_punto
   Que hace: navega hacia coordenadas [x, z] corrigiendo rumbo automaticamente.
   Consecuencia: el barco avanza hacia el punto.
   Parametro: lista [x, z].

3) frenar
   Que hace: reduce la velocidad a aproximadamente 0.3 nudos.
   Consecuencia: el barco desacelera progresivamente. NO se detiene de golpe.
   Parametro: ninguno (null).

4) terminar
   Que hace: declara la mision cumplida.
   Consecuencia: la mision se cierra.
   Parametro: ninguno (null).
   Restriccion: SOLO valida si la distancia a meta es menor a 15 metros.

=== ACCIONES ADMISIBLES EN ESTA FASE ===
{admisibles}
{nota_adm}

=== TAREA ===
Analiza el estado y elegi la accion que mejor contribuya a cumplir la mision.

Responde UNICAMENTE con JSON, sin texto adicional:
{{"accion": "<nombre>", "parametro": <valor o null>}}
"""


def prompt_VC(meta_x, meta_z, pos_x, pos_z, hdg, sog, dist, rumbo_meta, viento_kn=0.0, viento_dir=0.0):
    """VB + enfasis visual: mayusculas y separadores."""
    desv = _desvio(rumbo_meta, hdg)
    fase = _fase(dist)
    linea_viento = f"  VIENTO: {viento_kn:.1f} nudos desde {viento_dir:.0f} grados\n" if viento_kn > 0 else ""

    if dist < 15.0:
        admisibles = "corregir_rumbo, ir_a_punto, frenar, terminar"
        nota_adm = "TODAS las acciones son admisibles en esta fase."
    else:
        admisibles = "corregir_rumbo, ir_a_punto, frenar"
        nota_adm = "terminar NO es admisible: el barco aun NO esta en el radio de llegada (<15m)."

    return f"""=================================================================
TIMONEL DE VELERO AUTONOMO
=================================================================

>>> PROPOSITO <<<
Llevar el barco hasta la meta de forma segura.
La mision se completa cuando el barco esta DENTRO DE 15 METROS de la meta.

>>> ESTADO ACTUAL <<<
  POSICION:      ({pos_x:.1f}, {pos_z:.1f})
  META:          ({meta_x:.1f}, {meta_z:.1f})
  DISTANCIA:     {dist:.1f} METROS
  FASE:          {fase}
  HEADING:       {hdg:.1f} grados (0=N, 90=E)
  RUMBO A META:  {rumbo_meta:.1f} grados
  DESVIO:        {desv:.1f} grados
  VELOCIDAD:     {sog:.2f} nudos
{linea_viento}
>>> ACCIONES DISPONIBLES <<<

[1] corregir_rumbo
    Hace: gira la proa a un angulo absoluto 0-360.
    Efecto: reorienta sin avanzar.
    Parametro: angulo en grados.

[2] ir_a_punto
    Hace: navega hacia [x, z] corrigiendo rumbo.
    Efecto: avanza hacia el punto.
    Parametro: [x, z].

[3] frenar
    Hace: reduce velocidad a ~0.3 nudos.
    Efecto: desacelera progresivamente.
    Parametro: null.

[4] terminar
    Hace: declara mision cumplida.
    Efecto: cierra la mision.
    Restriccion: SOLO si DISTANCIA < 15 METROS.
    Parametro: null.

>>> ACCIONES ADMISIBLES EN ESTA FASE <<<
  {admisibles}
  {nota_adm}

=================================================================
>>> TAREA <<<
Elegi la accion que mejor contribuya al proposito dado el estado actual.

Responde UNICAMENTE con JSON, sin texto adicional:
{{"accion": "<nombre>", "parametro": <valor o null>}}
=================================================================
"""


def prompt_VD(meta_x, meta_z, pos_x, pos_z, hdg, sog, dist, rumbo_meta, viento_kn=0.0, viento_dir=0.0):
    """VB + few-shot: 4 ejemplos resueltos, uno por accion."""
    desv = _desvio(rumbo_meta, hdg)
    fase = _fase(dist)
    linea_viento = f"- Viento: {viento_kn:.1f} nudos desde {viento_dir:.0f} grados\n" if viento_kn > 0 else ""

    if dist < 15.0:
        admisibles = "corregir_rumbo, ir_a_punto, frenar, terminar"
        nota_adm = "(todas las acciones son admisibles en esta fase)"
    else:
        admisibles = "corregir_rumbo, ir_a_punto, frenar"
        nota_adm = "(terminar NO es admisible: el barco aun no esta en el radio de llegada)"

    ejemplos = """EJEMPLOS RESUELTOS (4 acciones, distintos estados):

Ejemplo 1 - desalineado:
  Estado: dist=120m, desvio=90 grados, sog=4kn
  Decision: {"accion": "corregir_rumbo", "parametro": 45.0}

Ejemplo 2 - alineado:
  Estado: dist=100m, desvio=5 grados, sog=5kn
  Decision: {"accion": "ir_a_punto", "parametro": [100.0, 100.0]}

Ejemplo 3 - a la deriva:
  Estado: dist=80m, desvio=20 grados, sog=7kn
  Decision: {"accion": "frenar", "parametro": null}

Ejemplo 4 - en la meta:
  Estado: dist=8m, desvio=15 grados, sog=1kn
  Decision: {"accion": "terminar", "parametro": null}
"""

    return f"""Sos el timonel de un velero autonomo. Tu objetivo es completar la mision de navegacion.

=== PROPOSITO ===
Llevar el barco hasta la meta de forma segura y eficiente.
La mision se completa cuando el barco esta dentro de 15 metros de la meta.

=== ESTADO ACTUAL ===
- Posicion: ({pos_x:.1f}, {pos_z:.1f})
- Meta: ({meta_x:.1f}, {meta_z:.1f})
- Distancia a meta: {dist:.1f} metros
- Heading (proa): {hdg:.1f} grados (0=norte, 90=este)
- Rumbo hacia la meta: {rumbo_meta:.1f} grados
- Desvio actual: {desv:.1f} grados
- Velocidad: {sog:.2f} nudos
{linea_viento}
=== ACCIONES DISPONIBLES ===

1) corregir_rumbo: gira la proa a un angulo absoluto (0-360).
2) ir_a_punto: navega hacia coordenadas [x, z].
3) frenar: reduce velocidad a ~0.3 nudos.
4) terminar: declara mision cumplida. SOLO valida si dist < 15m.

=== ACCIONES ADMISIBLES EN ESTA FASE ===
{admisibles}
{nota_adm}

{ejemplos}

=== TAREA ===
Elegi la accion que mejor contribuya al proposito dado el estado actual.

Responde UNICAMENTE con JSON, sin texto adicional:
{{"accion": "<nombre>", "parametro": <valor o null>}}
"""
