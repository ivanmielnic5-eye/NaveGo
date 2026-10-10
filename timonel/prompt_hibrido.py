#!/usr/bin/env python3
"""prompt_hibrido.py - Prompt del sistema hibrido.

Diferencia clave con las variantes anteriores: el LLM SOLO ve las acciones
admisibles en el estado actual, no las 4. Eso reduce el espacio de decision.

Referencia: EXPEDIENTE/80 seccion 6.
"""


def _desvio(rumbo_meta, hdg):
    return abs((rumbo_meta - hdg + 540) % 360 - 180)


def prompt_hibrido(meta_x, meta_z, pos_x, pos_z, hdg, sog, dist, rumbo_meta,
                   admisibles, viento_kn=0.0, viento_dir=0.0):
    """Prompt con acciones admisibles filtradas.

    Args:
        admisibles: lista de strings con las acciones admisibles.
    """
    desv = _desvio(rumbo_meta, hdg)
    linea_viento = f"- Viento: {viento_kn:.1f} nudos desde {viento_dir:.0f} grados\n" if viento_kn > 0 else ""

    # Descripciones por accion
    descripciones = {
        "corregir_rumbo": "corregir_rumbo: gira la proa a un angulo absoluto (0-360). Parametro: grados.",
        "ir_a_punto": "ir_a_punto: navega hacia coordenadas [x, z]. Parametro: [x, z].",
        "frenar": "frenar: reduce velocidad a ~0.3 nudos. Parametro: null.",
        "terminar": "terminar: declara mision cumplida. Parametro: null.",
    }

    lista_adm = "\n".join([f"  {i+1}) {descripciones[a]}" for i, a in enumerate(admisibles)])

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
=== ACCIONES ADMISIBLES EN ESTE ESTADO ===
{lista_adm}

=== TAREA ===
Elegi UNA de las acciones admisibles que mejor contribuya al proposito.

Responde UNICAMENTE con JSON, sin texto adicional:
{{"accion": "<nombre de una accion admisible>", "parametro": <valor o null>}}
"""
