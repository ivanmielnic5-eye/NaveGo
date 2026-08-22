# SESION STATE MACHINE — NaveGo

Actualizado: 2026-08-22

## Objetivo
Definir el ciclo de vida de una derrota para eliminar ambiguedades entre pausar, finalizar, resetear y continuar.

## Estados
EN_ESPERA: la app esta abierta pero no registra distancia.
REGISTRANDO: la derrota esta activa y se acumula distancia.
EN_PAUSA: la derrota esta activa pero no registra distancia.
FINALIZADA: la derrota fue cerrada y no admite reanudar.

## Flujo
EN_ESPERA
  -> iniciar -> REGISTRANDO
REGISTRANDO
  -> pausar -> EN_PAUSA
  -> finalizar -> FINALIZADA
EN_PAUSA
  -> reanudar -> REGISTRANDO
  -> finalizar -> FINALIZADA
FINALIZADA
  -> resetear -> EN_ESPERA

## Reglas
1. Al abrir NaveGo, inicia en EN_ESPERA. No cuenta distancia.
2. Solo se registra distancia en REGISTRANDO.
3. Pausa no suma distancia. Al reanudar se marca un nuevo segmento.
4. Finalizar solo es valido si hay sesion activa.
5. Luego de finalizar, no debe existir boton reanudar.
6. Resetear borra contadores y deja en EN_ESPERA.
7. Si ya existe una referencia para la sesion, no se crea otra.
8. El historial debe tener scroll propio y no quedar oculto bajo Android.

## Indicador visual sugerido
EN_ESPERA: texto neutro, sin acumulador activo.
REGISTRANDO: punto verde activo.
EN_PAUSA: punto amarillo.
FINALIZADA: punto cian y opcion de guardar referencia.

