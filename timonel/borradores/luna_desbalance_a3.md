<!-- ingesta: 2026-10-13 20:47 -->
# BORRADOR — LUNA: DESBALANCE DE LABELS EN A3

**Fecha:** 2026-10-13
**Estado:** BORRADOR.
**Origen:** consulta sobre el desbalance 33/67 en el banco A3.

---

## 1. Recomendacion: C como base, con una cuarta opcion

No alteraria F2 retroactivamente para forzar un 50/50. El desbalance
surge del diseno de cuadrantes, no de un error de etiquetado.

- A: No recomiendo. Duplicar Q1 altera su peso y puede introducir
  ejemplos repetidos que inflen el rendimiento.
- B: No recomiendo como solucion principal. Reduce datos y cobertura
  de Q2-Q4.
- C: Si. Conservar el banco y publicar el baseline mayoritario real:
  0.667 en train y 0.714 en test_interp.
- D: Recomiendo anadir un test de evaluacion balanceado, separado del
  test representativo original. Asi se mide tanto el rendimiento bajo
  la distribucion disenada como la capacidad de distinguir ambas
  etiquetas sin ventaja por prevalencia.

## 2. Ponderar Q1?

Ponderar la perdida durante el entrenamiento puede ayudar a compensar
el desbalance, pero no corrige la distribucion del test ni sustituye
un baseline adecuado. Debe declararse como parte del protocolo.

Reportaria exactitud total, exactitud por etiqueta (terminar, ir_a),
balanced accuracy y resultados por cuadrante. Mantendria ambos tests
separados; no mezclaria metricas en una sola cifra.

## 3. Criterio de exito e intervalos de confianza

El criterio "0.99 por familia con IC >= 0.97" no exige matematicamente
un banco 50/50, siempre que se evalue cada familia por separado y con
intervalos apropiados.

Exige precisar que significa familia: etiqueta, cuadrante o tipo de
regla. La metrica agregada puede ocultar fallos de la clase
minoritaria.

Antes de aprobar el criterio: fijar la unidad de evaluacion, el
metodo del intervalo de confianza y el minimo de muestras por
familia. Si cada familia debe alcanzar el umbral independientemente,
ninguna puede compensar los errores de otra.
