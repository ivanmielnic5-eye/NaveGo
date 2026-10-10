# 01 — Proyecto

## Identidad
- Nombre repo: navego_recuperado
- Path: ~/navego_recuperado
- Dominio: tracker GPS (replay, gaps, telemetría viva, persistencia SQLite)
- Stack: React Native / Expo + TypeScript + SQLite

## Objetivo macro
Separar el "cerebro" del tracker (lógica pura, testeable, reusable)
de sus "efectos" (UI y persistencia), sin cambiar semántica observable.

## Objetivo del refactor en curso
Un callback de ~140 líneas en useNaveGoTracker.ts hace 16 cosas mezcladas.
Lo estamos partiendo en:
  - processFix(input, state) → ProcessResult   (puro, sin efectos)
  - publishUiResult(result, location)          (solo UI)
  - persistFixResult(result, location)         (solo SQLite)

## Por qué importa
Habilita el plan de background (Fase 0):
procesar fixes fuera del hilo de UI, con lógica determinista y verificable.

## Restricción dura
Preservar semántica al 100%. Si hay duda, se conserva el comportamiento
viejo aunque parezca subóptimo. Los cambios "de paso" NO van en este refactor.
