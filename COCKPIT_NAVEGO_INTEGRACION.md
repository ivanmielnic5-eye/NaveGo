# COCKPIT NAVEGO — Estrategia de Integracion

Actualizado: 2026-08-19

## Principio
NaveGo es un Project Adapter, no el centro del sistema.
El Core no debe conocer GNSS, SOG, COG ni SQLite.
La integracion debe ser gradual, segura y reversible.

## Arquitectura objetivo
Cockpit -> Core Kernel -> Contrato Universal -> NaveGo Adapter -> Tracker/SQLite/HUD.

## Separacion de experiencias
- NaveGo HUD: instrumento para el navegante.
- Cockpit: instrumento para el Director y la IA.
- NaveGo Adapter: puente entre ambos mundos.
No conviene que una pantalla haga ambas cosas.

## Frontera explicita
Crear NaveGoProjectAdapter como traductor oficial.
Convierte GNSS, COG, SOG, distancia, sesiones, tracking en conceptos universales.

## Regla sagrada
El Core jamas recibe GNSS.
Recibe Health Component generico: "navegacion / estado: degradado".
El Adapter decide el significado universal.

## Traductores del Adapter
State Adapter: estado del proyecto, mision, sesion.
Work Adapter: trabajo actual, registrar derrota.
Evidence Adapter: que constituye evidencia.
File Adapter: referencias a sesiones y documentos.
Action Adapter: acciones por niveles de riesgo.

## Acciones por niveles
Nivel 1: lectura (abrir, consultar).
Nivel 2: reversibles (centrar, cambiar pantalla).
Nivel 3: operativas (iniciar, pausar, finalizar).
Nivel 4: criticas (modificar persistencia, configuracion).
Las criticas requieren confirmacion explicita.

## SQLite permanece del lado NaveGo
Cockpit -> NaveGo Adapter -> NaveGo persistence -> SQLite.
El Core no sabe que existe SQLite.

## Pantalla CockpitScreen no conoce NaveGo
CockpitScreen -> Cockpit Core Model -> Project Adapter -> NaveGo.
No debe importar tracker.currentSog ni SQLite directamente.

## Fases de integracion
Fase 0: Congelar HUD actual como referencia. Riesgo Bajo.
Fase 1: Crear frontera NaveGoProjectAdapter. Riesgo Bajo.
Fase 2: Exponer estado en modo lectura. Riesgo Bajo.
Fase 3: Exponer evidencia. Riesgo Bajo.
Fase 4: Exponer trabajo/sesion. Riesgo Bajo.
Fase 5: Conectar archivos vivos. Riesgo Medio.
Fase 6: Conectar historial. Riesgo Medio.
Fase 7: Acciones de lectura. Riesgo Bajo.
Fase 8: Acciones reversibles. Riesgo Medio.
Fase 9: Acciones operativas. Riesgo Alto.
Fase 10: Acciones criticas. Riesgo Alto.

## Proximos pasos inmediatos
Implementar solo Fase 0, Fase 1 y Fase 2.
Probar que el Cockpit puede ver el estado real de NaveGo sin romper nada.

## Relacion con PROJECT_STATE.md
Estado operacional: viene del sistema vivo (tracking activo).
Estado documental: viene de PROJECT_STATE.md (Course-Up experimental).
No mezclarlos.
El Cockpit puede mostrar ambos separados.

## Flujo completo
Humano -> Cockpit UI -> Cockpit Core -> Contrato Universal -> NaveGo Adapter -> Tracker/SQLite/HUD.
En sentido inverso: NaveGo -> estado/eventos/evidencia/capacidades -> Adapter -> Cockpit -> Humano.

## Criterio de exito
El Cockpit debe poder leer el estado real de NaveGo sin que NaveGo se entere de que existe un Cockpit.
