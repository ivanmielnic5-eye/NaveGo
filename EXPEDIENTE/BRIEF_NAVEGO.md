# Brief de arranque — NAVEGO

Generado: 2026-10-09T22:17:21-03:00

---

## 1. Identidad
- Proyecto: NAVEGO
- Repo: /home/ivan/navego_recuperado
- Rama: experimento-v4-admin
- HEAD: a984d4b
- Nombre: NaveGo
- Tipo: navigation

## 2. Estado del contexto
- gate_status: WARNING
- drift: WARNING (optional: simulator_source(STALE:6b110d01!=d4b93f07))

## 3. Mision y fase
- Objetivo: Sistema de navegacion autonomo, offline, soberano
- Fase: desarrollo
- Estado: OPERATIVO
- Riesgo: verde

## 4. Estado actual

Funciona (verificado):
- Captura en primer plano.
- Captura en segundo plano (pantalla apagada).
- Retoma de sesion tras reinicio del celular.
- Finalizar + reabrir -> boton INICIAR.
- Cerrar sin finalizar + reabrir -> retoma sesion.

Pendiente (bugs finos):
- Track honesto (amarillo/negro) no aparece en el mapa.
- SOG en 0.3 estando quieto.
- Movimientos lentos (4-5 m) no se contabilizan.

## 5. Trabajo activo
- Hipotesis: H-2026-0023
  Cierre del hito de background: bugs finos + recuperacion del track honesto
- Proximo paso: Fix de SOG en reposo, reconectar getGapsSince al polling, y cierre de LOGOS v1.1
- Ultima decision: Implementacion de LOGOS v1.1 (logos-reconcile + drift detection + logos-brief). Pendiente: registrar formalmente como D-XXXX en el registro instituido (ubicacion por confirmar).

## 6. Restricciones activas
- No tocar GNSS sin hipotesis previa
- Un cambio a la vez
- No inventar datos que no tengo
- Verificar antes de asumir
- No elegir formato de mapa sin medir
- R-09: quien propone no cierra la rama
- R-18: source of truth

## 7. Pendientes priorizados
- Track honesto — pérdida por migración Doc 46
- Field log no se escribe tras reinicio del celular
- Diseño pendiente: jerarquía de confianza de fuentes para cartas náuticas
- Auto-commit WIP en logos-arranque
- Blender MCP — velas dinamicas + timon + mastil no rigido

## 8. Comandos operativos

Ver estado del contexto:
```
.logos/bin/logos-gate NAVEGO
```

Regenerar capsula:
```
.logos/bin/logos-mem NAVEGO
```

Marcar una fuente como revisada:
```
.logos/bin/logos-reconcile mark-reviewed <type>
```

Build de la app (release):
```
cd ~/navego_recuperado
unset EXPO_PUBLIC_GNSS_REPLAY
unset EXPO_PUBLIC_GNSS_BACKGROUND_TEST
unset EXPO_PUBLIC_GNSS_TASK_PRODUCER
npx expo run:android --variant release
```

## 9. Reglas duras de trabajo
- Backup explicito .pre-<etapa> antes de tocar codigo.
- Un paso por vez. Verificar despues de cada cambio.
- Comandos con bloque de copiar/pegar claro.
- El codigo va al chat, no a bash.
- Los .pre-* de backup NUNCA se borran sin permiso.
- Hablar en criollo primero, despues el termino tecnico.
- No proponer cambios hasta que el Director diga 'vamos'.
- El sistema NO MIENTE. No inventa datos.
- Verificar toda cita de LLM antes de apoyarse en ella.

## 10. Simulador Godot

- Path: ~/interfaz/
- Rama: experimento-godot
- HEAD: e30c123
- Ultimo commit: e30c123 Blender: archivo de trabajo de Polaris con velas separadas (hace 20 horas)
- reviewed_against_hash: 6b110d01bc538669...

Hipotesis del simulador (domain=simulator):
- (ninguna registrada todavia)

Comandos del simulador:
```
cd ~/interfaz/
git log --oneline -5
git status -s
```

