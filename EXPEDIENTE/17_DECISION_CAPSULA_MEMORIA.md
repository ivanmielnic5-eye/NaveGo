# DECISIÓN PROVISIONAL — Cápsula de Memoria

**Fecha:** 2026-09-22
**ID:** D-LOGOS-MEM-001
**Estado:** PROPUESTA / PROVISIONAL
**Revisión pendiente:** crítica de GPT-4

---

## Propósito

Generar una representación pequeña, autocontenida y reutilizable del
estado esencial de un proyecto, para iniciar una nueva sesión de IA
sin depender de la memoria del hilo anterior.

## Separación de roles

- Documento generado:     capsula-de-memoria.md
- Componente conceptual:  Sistema de Cápsula de Memoria
- Comando canónico:       logos-mem
- Comando atajo:          mem

## Contenido de la cápsula

La cápsula es un MECANISMO DE CONTINUIDAD COGNITIVA, no solo
una tarjeta de contexto. Incluye:

- Proyecto (identidad).
- Estado actual.
- Trabajo activo.
- Hipótesis activa (las que estén EN_CURSO en el kernel).
- Decisiones pendientes (las que bloquean o vencen pronto).
- Restricciones operativas (específicas del trabajo activo).
- Fuentes de verdad declaradas por el MANIFEST.
- Reglas críticas.

La cápsula es DERIVADA. No es fuente de verdad. Se regenera desde
las fuentes autoritativas. Si la cápsula se corrompe, se regenera.

## Arquitectura

FUENTES AUTORITATIVAS (MANIFEST + EXPEDIENTE + kernel)
     ↓
logos-mem (generador)
     ↓
CÁPSULA DE MEMORIA
     ↓
chat nuevo / agente local
     ↓
CONTEXT GATE
     ↓
READY / BLOCKED
     ↓
DSH o chat

La cápsula resuelve CONTINUIDAD.
El Gate resuelve AUTORIZACIÓN.
Son problemas distintos.

## Decisión provisional (3 acuerdos)

1. Nombre: "Cápsula de Memoria" para el documento y el componente.
   Comando separado: logos-mem (canónico) + mem (atajo).
2. Contenido: mecanismo de continuidad cognitiva completo
   (hipótesis + decisión + restricciones incluidas).
3. Estado: PROVISIONAL hasta crítica de GPT-4.

## Revisión pendiente

GPT-4 debe criticar:
- ¿Es correcto incluir hipótesis/decisión/restricciones, o satura?
- ¿El tamaño se mantiene bajo control?
- ¿Hay algo que falte o sobre?

## Regla asociada

R-09: quien propone no cierra la rama.
Esta decisión fue propuesta por DeepSeek. La revisa GPT-4. La
aprueba el Director (Iván).
