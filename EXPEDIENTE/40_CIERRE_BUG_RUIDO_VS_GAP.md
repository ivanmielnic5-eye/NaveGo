# CIERRE BUG RUIDO vs GAP

**Fecha:** 2026-09-25
**Estado:** CERRADO
**Resultado:** NO SE REPRODUCE en el TCL real

---

## Contexto

Se investigo si el ruido de posicion del GPS podia generar
saltos > 15 m que el tracker confundiera con gaps.

En simulador (sigma=3 m), DSH midio ~22 falsos gaps por hora.
Eso llevo a proponer una regla para distinguir ruido de gap.

## Investigacion

1. DSH corrio experimento en simulador. Encontro el bug y
   propuso regla: esGapReal = (dt > 2 s) O (speed <= 0.3).

2. GPT hizo critica conceptual. DSH acepto 5 criticas y
   redisenio la propuesta: separar gap temporal, outlier
   espacial, y ruido. Umbral dinamico, no fijo.

3. Se aprobo hacer test en TCL real antes de implementar
   cualquier cambio (zona roja: GNSS/distancia).

4. Se capturo el primer dataset del TCL T610P (321 fixes).
   Sesion en pasillo techado, patio con cielo, e interior.

## Hallazgo del TCL real

| Metrica | Simulador | TCL real |
|---|---|---|
| accuracy mediano | 4.5 m | 1.77 m |
| dt mediano | 1.0 s | 1.0 s |
| Saltos > 15 m | Decenas | 1 en 321 |

**El TCL es mas limpio que el simulador.**

El unico salto > 15 m tiene dt=1 s y speed=0. Se clasifica
igual con el codigo actual que con la regla propuesta.
No hay informacion para discriminar.

## Decision

NO IMPLEMENTAR el fix del ruido. Razones:

1. El bug no se reproduce con datos reales del TCL.
2. El dataset no valida ni refuta la regla propuesta.
3. El unico caso ambiguo (salto i=23) se comporta igual con
   ambos criterios.
4. Tocar la zona roja (GNSS/distancia) sin evidencia clara
   es riesgo innecesario.

## Lo que queda como pendiente

Si en algun momento se captura un dataset con un gap REAL
(tunel, estacionamiento subterraneo, corte genuino de varios
segundos), se puede reabrir la investigacion. Con el dataset
actual, no hay evidencia para cambiar.

## Referencias

- docs/gnss/tcl_field/ANALISIS_TCL_FIELD_01.md
- docs/gnss/exp_ruido_vs_gap/INFORME_RUIDO_VS_GAP.md
- .logos/dsh-output/revision_ruido_gpt_20260925_1849.log
- .logos/dsh-output/analisis_tcl_field_20260925_2151.log
- EXPEDIENTE/39_DECISION_RUIDO_VS_GAP.md

---

*Generado: 2026-09-25*
*Por: DeepSeek (chat) bajo direccion del Director*
