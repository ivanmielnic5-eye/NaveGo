# COCKPIT UNIVERSAL — Estructura de Repositorio

Actualizado: 2026-08-19

## Principio
NaveGo es un adaptador de prueba, no la definicion del sistema.
El Core no debe conocer detalles de GNSS, COG, SOG o SQLite.

## Estructura propuesta
/cockpit
/cockpit/core
/cockpit/system
/cockpit/adapters/navego
/cockpit/adapters/gaia
/cockpit/ui

## Responsabilidades

### core
Contiene el contrato universal.
Los 5 modulos: ESTADO, TRABAJO, EVIDENCIA, ARCHIVOS, ACCION.
Estados universales: ESTABLE, EXPERIMENTAL, BLOQUEADO, NO_VERIFICADO.
Estados de conocimiento: IMPLEMENTADO, PROBADO, OBSERVADO, VALIDADO.
Riesgo: BAJO, MEDIO, ALTO.

### system
Maneja la salud del sistema, eventos y procesos.
Se conecta con scripts y archivos vivos.
Monitorea: procesos, servicios, conectividad, recursos.

### adapters/navego
Traduce el dominio nautico al lenguaje del Core.
Expone: GNSS, COG, SOG, derrota, orientacion.
Convierte datos en el formato del Data Contract.

### adapters/gaia
Futuro adaptador de ejemplo.
Expone: camara, pipeline, dataset, detector.

### ui
Componentes visuales genericos.
Dock, Header, StatusLights, MissionBar, AreaPrincipal.
No debe importar logica especifica de ningun adaptador.

## Mecanismo de configuracion
Se propone un archivo de configuracion que indique que adaptadores estan activos.
Ejemplo: adapters activos = navego.

## Integracion con archivos vivos
El Cockpit no duplica informacion.
Lee y actualiza: PROJECT_STATE.md, DECISIONS.md, TEST_LOG.md, CHANGE_LOG.md.
Los archivos vivos son la fuente de verdad.

## Integracion con NaveGo
El adaptador navego reutiliza useNaveGoTracker, SQLite y mapas existentes.
Traduce los datos al formato universal sin romper la arquitectura.

## Proximos pasos
1. Crear la carpeta cockpit con subcarpetas core, system, adapters, ui.
2. Implementar Fase 1 del Core: tipos y constantes universales.
3. Implementar primer adaptador navego minimo.
4. Conectar la UI existente al Core mediante el adaptador.

