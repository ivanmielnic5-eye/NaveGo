# BORRADOR — LUNA: VERIFICACION DE FUENTES (resumen)

**Fecha:** 2026-10-13
**Estado:** BORRADOR. Fuera del expediente hasta validacion con Claude.
**Origen:** verificacion de los 4 papers reportados por Notebook LLM.

---

## Los 4 papers: existen

1. **AgentVerify** — DOI 10.20944/preprints202604.1029.v1.
   Eric Fang, abril 2026. Preprint, no revisado por pares.
   Numeros: 13.33% verificador neural, 86.67% LTL, 80% contratos,
   46.67% sin logica temporal. Resultados de 15 escenarios, no ley.

2. **MAGS** — arXiv:2609.19391v1.
   Wu, Roberts, Huang, Lin, Friedman, Cho, Orlanski, Sala
   (Wisconsin + Princeton), sept 2026. Preprint.
   Numeros: 100% certificados Dafny (220/220), pero 18/100 fallaron
   auditoria externa SecCodePLT. El certificado formal no cubre todo.

3. **Constraint Drift** — arXiv:2605.10481v1.
   Li, Ma, Wen, Huang, Zhou, Fu, Cheng (Liverpool + Nottingham +
   Exeter + Tokio), mayo 2026. Preprint.
   Es posicion conceptual, no tasa de degradacion medida.

4. **Survey** — arXiv:2608.14590v1.
   Dantas, Cordeiro, Nowroozi, Norbert (Manchester + Greenwich +
   TII), junio 2026. Preprint.
   Verifier tax: 94% interceptado, SSR <5%. Pero de un solo estudio
   (TRIAD-SAFETY en tau-Bench), sin replicacion, certeza baja.

## Los 5 conceptos: hipotesis de diseno

1. **Arquitectura 3 capas** — respaldo preliminar.
2. **Constraint drift** — concepto publicado, evidencia preliminar.
3. **Verificacion composicional** — respaldo preliminar.
4. **Verifier tax** — reportado, certeza baja, sin replicacion.
5. **Captain-in-the-loop** — respaldo parcial.

## Regla

- Concepto: se registra como hipotesis de diseno.
- Numero: no se cita hasta verificar el estudio primario.
- Aplicacion a NaveGo: se prueba con experimentacion propia.

## Pendiente

- Claude valida (18hs).
- Verificar estudio primario del verifier tax (TRIAD-SAFETY).
