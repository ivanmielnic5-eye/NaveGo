# H-2026-09-26 — Track de referencia pierde marcas de gap al iniciar trayecto nuevo

**Fecha de registro:** 2026-09-26
**Estado:** ABIERTO — pendiente de trabajo en sesion futura
**Prioridad:** mejora funcional / consistencia visual (no critica)

---

## Comportamiento observado (incorrecto)

1. Se carga una sesion guardada como referencia superpuesta.
2. Se ve bien: segmentos celestes + segmentos amarillo/negro (gaps GNSS).
3. Se apreta INICIAR TRAYECTO para comenzar uno nuevo.
4. Los segmentos amarillo/negro de la referencia DESAPARECEN.
   Solo queda visible lo celeste. El track de referencia queda incompleto.

## Comportamiento esperado

El track de referencia debe conservar TODOS sus segmentos
al iniciar un trayecto nuevo, incluyendo los tramos amarillo/negro
que marcan gaps GNSS.

## Semantica del tramo amarillo/negro — IMPORTANTE

El tramo amarillo/negro NO afirma que el barco paso por esa recta.
NO dice "vos pasaste por aca".

Significa: "aca falta informacion. No sabemos que hizo el barco
en ese momento. Pudo haber ido recto, pudo haber dado una vuelta
completa, pudo haber ido por otro lado."

La recta es un relleno simbolico para no dejar un hueco visual
entre dos fixes separados por un gap. NO es una asercion de
trayectoria.

El sistema NO miente: no inventa metros, no inventa forma del
recorrido. Solo dice "aqui hubo un gap, no tenemos la traza".

## Distancia

El tramo amarillo/negro NO se suma como distancia recorrida.
La distancia real registrada excluye esos segmentos. Es coherente
con la semantica: si no sabemos que hizo el barco, no podemos
afirmar cuantos metros recorrio.

## Fuera de alcance

- No es el estado DETENIDO de la captura (eso fue confusion inicial,
  no aplica).
- No afecta captura, persistencia ni logica de gaps.
- Solo afecta la capa de visualizacion de sesion de referencia.

## No hacer todavia

Este hallazgo se registra para trabajo futuro. No se toca
codigo hasta que el Director lo indique.

## Contexto visual

Capturas tomadas el 2026-09-26 15:01.
- Captura 1: track de referencia con segmentos amarillo/negro visibles.
- Captura 2: despues de INICIAR TRAYECTO, los segmentos amarillo/negro
  de la referencia desaparecieron.

