# DECISION — RUIDO vs GAP

**Fecha:** 2026-09-25
**Estado:** PROPUESTA — pendiente de test del TCL

---

## Contexto

DSH detecto que a sigma >= 3.0 m, el ruido de posicion puede
generar saltos > 15 m que el tracker confunde con gaps. Eso
genera falsos GapEvents y contamina la semantica del sistema.

## Decisiones aprobadas

1. **No implementar todavia el fix del ruido.** Requiere medicion
   real del TCL T610P primero.

2. **No implementar todavia el fix P2 (gaps chicos).** DSH demostro
   que el "fix" no aporta en simulador. Pendiente de medir en campo.

3. **Aprobar el nuevo diseno de deteccion** con tres fenomenos
   separados:
   - Gap temporal: dt > T_gap (2 s).
   - Outlier espacial: dt normal + salto > umbral dinamico.
   - Ruido/jitter: saltos chicos repetidos.

4. **Umbral dinamico, no fijo.** El 15 m universal pasa a ser
   funcion del perfil: p95(SOG) * dt + k * accuracy.

## Orden de acciones

1. Test del TCL en 3 situaciones (quieto, movimiento, degradado).
2. Analisis de los datos reales con DSH.
3. Recien entonces, decidir si implementar el fix.

## Referencias

- docs/gnss/exp_ruido_vs_gap/INFORME_RUIDO_VS_GAP.md
- .logos/dsh-output/revision_ruido_gpt_20260925_1849.log
- Critica conceptual de GPT (5 puntos)

---

*Generado: 2026-09-25*
*Por: DeepSeek (chat) bajo direccion del Director*
