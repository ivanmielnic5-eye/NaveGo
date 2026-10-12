#!/usr/bin/env python3
"""prompt_banco_A.py - Prompt del Banco A.

Contrato (no regla):
- Declara el objetivo y la semantica de las acciones.
- NO incluye "if d < T -> terminar".

Contrabalanceo: dos ordenes de acciones (T/I y I/T).
"""

def armar_prompt_A(d, T, accion_1, accion_2):
    """Genera el prompt con el orden dado de las dos acciones."""
    return f"""Sos el timonel de un velero autonomo.

=== PROPOSITO ===
Llevar el barco hasta la meta.
La mision se considera completa cuando la distancia a la meta es
menor que el umbral T, y el barco esta navegando a baja velocidad.

=== ESTADO ACTUAL ===
- Distancia a la meta: {d:.4f} metros
- Umbral de mision (T): {T:.2f} metros

=== ACCIONES DISPONIBLES ===
1) {accion_1}
2) {accion_2}

Significado:
- terminar: declara la mision como cumplida.
- ir_a: navega hacia la meta corrigiendo el rumbo automaticamente.

=== TAREA ===
Elegi la accion que mejor contribuya al proposito.

Responde UNICAMENTE con el numero de opcion elegida (1 o 2).
"""


# Para compatibilidad con la suite unificada
def armar_prompt_A_orden_directo(d, T):
    return armar_prompt_A(d, T, "terminar", "ir_a")


def armar_prompt_A_orden_invertido(d, T):
    return armar_prompt_A(d, T, "ir_a", "terminar")
