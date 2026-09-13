# CICLO DE SESIONES — NaveGo

Actualizado: 2026-08-22

## Objetivo
Definir el ciclo de vida correcto de una derrota para resolver acumulacion,
unicidad y mutacion de datos historicos.

## Estados de operacion
1. AMARRE: app abierta, tracking inactivo, sin acumular distancia.
2. INICIAR DERROTA: crea nueva sesion en SQLite y comienza a registrar.
3. TRACKING ACTIVO: acumula distancia y registra fixes GPS.
4. PAUSAR: detiene registro, no suma distancia, crea marcador de pausa.
5. REANUDAR: inicia segmento nuevo, mantiene sesion actual.
6. FINALIZAR: cierra sesion, guarda distancia final, vuelve a AMARRE.

## Regla de pausa (Opcion C)
- Durante la pausa no se suma distancia.
- Al reanudar se inicia un segmento nuevo.
- El mapa debe mostrar una interrupcion visible, no una linea recta falsa.
- Solo se registra lo navegado despues de soltar amarras.

## Reglas de persistencia
- Cada sesion cerrada es inmutable.
- Una sesion nueva debe tener id unico.
- La secuencia de GPS se reinicia solo al crear sesion nueva.
- No se puede crear mas de una referencia para la misma sesion.
- Si la referencia ya existe, el sistema debe avisar.

## Mapeo con codigo actual
- startTracking: crea sesion y comienza a registrar.
- togglePause: pausa/reanuda registro.
- stopTracking: cierra sesion y guarda distancia.
- resetTracking: limpia contadores en memoria.
- createReferenceRouteFromSession: crea referencia desde una sesion cerrada.

## Problemas actuales
- App inicia tracking automaticamente al abrir.
- Boton FINALIZAR no llama a stopTracking.
- Boton RESETEAR no cierra sesion activa.
- Pausa no crea marcador de pausa.
- Referencias duplicadas por doble toque.
- Lista de sesiones se desborda en pantalla.

## Intervenciones futuras
1. Agregar estado AMARRE en tracker.
2. Conectar FINALIZAR con stopTracking.
3. Conectar RESETEAR con cierre de sesion si corresponde.
4. Crear marcador de pausa en ruta y base de datos.
5. Impedir referencias duplicadas.
6. Corregir scroll de lista de sesiones.
