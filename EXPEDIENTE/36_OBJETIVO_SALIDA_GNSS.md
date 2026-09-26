# OBJETIVO DE SALIDA — INVESTIGACION CONTINUIDAD GNSS

**Fecha:** 2026-09-25
**Estado:** CONGELADO
**Decision asociada:** D-2026-0008

---

## La pregunta que responde esta investigacion

Cuando NaveGo pierde senal GNSS durante una travesia:

- Debe dejar el hueco marcado y seguir sin inventar nada?
- O necesita estimar la posicion durante el corte (dead reckoning)
  para que el track no se rompa?

## La salida esperada

Al terminar esta investigacion vamos a tener:

1. **Evidencia empirica** de que NaveGo (a) marca el hueco y sigue,
   o (b) necesita dead reckoning, o (c) ninguna de las dos cosas
   porque hay un tercer comportamiento que hoy no conocemos.

2. **Documentacion de que hace hoy el sistema** en 4 escenarios:

   - Escenario 1: corte corto (3 segundos)
   - Escenario 2: corte largo (30 segundos)
   - Escenario 3: multiples cortes en la misma sesion (3 cortes)
   - Escenario 4: giro durante el corte (barco cambia de rumbo)

3. **Metricas comparables** entre escenarios:
   - Distancia confirmada vs distancia real (del ground truth)
   - Cantidad de gaps registrados
   - Estado del sistema al volver la senal (continua, se congela, se rompe)
   - Coherencia visual del track (punto azul y linea roja)

## Lo que NO es objetivo de esta investigacion

- Construir dead reckoning completo (eso es consecuencia posible,
  no objetivo).
- Optimizar el simulador Godot (ya esta validado como laboratorio).
- Explorar nuevas capas de mapa.
- Investigar LIDR u otros metodos de interpolacion (eso viene despues,
  si la evidencia lo justifica).
- Mejorar la interfaz de usuario.

## Criterio de cierre

La investigacion se considera cerrada cuando:

1. Los 4 escenarios corrieron al menos una vez contra NaveGo real.
2. Los resultados estan guardados en expediente.
3. Existe una decision tomada (con evidencia) sobre si NaveGo
   necesita DR o no.

## Criterio de reapertura

Si despues de cerrar aparece un caso nuevo (por ejemplo, corte
de 10 minutos en travesia real) que revele comportamiento distinto
al documentado, la investigacion se reabre con un nuevo escenario.

---

*Firmado: Director*
*Redactado por: DeepSeek (chat), bajo direccion del Director*
