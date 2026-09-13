# COCKPIT UNIVERSAL — Plan de Implementacion

Actualizado: 2026-08-19

## Enfoque
Primero arquitectura, despues implementacion.
NaveGo sera adaptador de prueba, no definicion del sistema.

## Capas
1. Core: Estado, Trabajo, Evidencia, Archivos, Accion.
2. System: Salud, Eventos, Riesgo, Integraciones.
3. Project Adapters: NaveGo, GAIA, futuros proyectos.

## Componentes minimos
- Shell del Cockpit: contenedor general con header, area principal y dock.
- ModuloRenderer: muestra contenido segun modulo activo.
- StatusLightRow: fila de indicadores de salud dinamicos.
- MissionBar: estado de mision actual.
- Dock: cinco acciones universales.
- ContextualAI: capa de recomendacion contextual.

## Modelo de datos
- Archivos vivos: PROJECT_STATE.md, DECISIONS.md, TEST_LOG.md, CHANGE_LOG.md.
- Estado local: modulo activo, indicadores visibles, propuesta IA.
- No usar base de datos propia para el Cockpit.

## Mecanismo de actualizacion
- Lectura de archivos al entrar en un modulo.
- Refresco manual con boton o comando.
- Futuro: watcher o polling suave.

## Estrategia responsive
- Gramatica visual unica.
- PC: layout horizontal con columnas.
- Celular: dock inferior y contenido scrollable.
- No duplicar pantallas: adaptar componentes.

## Integracion con acciones
- Dock llama a scripts o funciones externas.
- Confirmacion obligatoria para acciones destructivas.
- Separar propuesta de IA de accion confirmada.

## Preparacion para voz
- Campo de intencion en modulo ACCION.
- Flujo: intencion, interpretacion, confirmacion, ejecucion.
- Voz sera otra entrada al mismo flujo.

## Fases de implementacion
Fase 1: Shell estatico con 5 modulos y dock.
Fase 2: Modulo Estado con lectura de PROJECT_STATE.md.
Fase 3: Modulo Trabajo con tarea activa y proximo paso.
Fase 4: Modulo Evidencia con estados de conocimiento.
Fase 5: Modulo Archivos con accesos a documentos.
Fase 6: Modulo Accion con campo de intencion.
Fase 7: Adaptador NaveGo como prueba.
Fase 8: Preparacion para voz.

## Criterios de aceptacion
En 2 segundos el usuario responde:
Que esta pasando?
Hay algun problema?
En que estamos trabajando?
Que esta comprobado?
Que puedo hacer ahora?

## Regla de oro
El Cockpit no muestra todo lo que sabe.
Muestra lo necesario para decidir que hacer despues.
