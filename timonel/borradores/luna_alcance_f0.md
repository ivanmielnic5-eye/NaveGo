<!-- ingesta: 2026-10-13 20:24 -->
# BORRADOR — LUNA: ALCANCE DE F0 TRAS EL GREP

**Fecha:** 2026-10-13
**Estado:** BORRADOR. Fuera del expediente hasta consolidar.
**Origen:** consulta sobre el alcance de F0 tras el grep de llamadores.

---

## 1. Alcance de F0: de acuerdo

Acotaria F0 al etiquetado offline de bancos. El grep de llamadores
cambia la evidencia arquitectonica: entrenador_v2.py es un evaluador
independiente, no parte del pipeline de etiquetado de A3.

Migrar ahora el entrenador y el runtime mezclaria alineacion
contractual con cambios de evaluacion y control. Los dejaria para
las fases posteriores, sin afirmar que esos componentes ya cumplen
F0.

## 2. Alcanza con migrar generar_banco_A2.py?

Si, si ese es el unico productor vigente de las etiquetas objeto de
F0.

- Debe delegar el etiquetado en etiquetar_por_T (o la interfaz
  canonica aprobada) y eliminar la logica local duplicada.
- Cada contexto debe suministrar su T correcto, sin fallback
  silencioso a 15.0.
- Verificar equivalencia sobre los 2316 contextos y probar
  explicitamente T=10, 15, 20, 25.
- Documentar entrenador y runtime como diferidos, indicando
  responsable/fase y literales pendientes.

## 3. Test guardian

No haria que el test de F0 falle por cada literal diferido de todo
el repositorio.

Recomiendo dos controles separados:

1. Guardian de F0: busca literales prohibidos en los archivos
   migrados y falla ante nuevas apariciones.
2. Inventario de deuda tecnica: registra las apariciones conocidas
   fuera del alcance, con archivo, semantica y fase prevista. Debe
   detectar apariciones nuevas no clasificadas.

Las excepciones explicitas por archivo pueden servir, pero una
excepcion no debe ocultar cualquier literal presente en ese archivo.
Conviene mantener una lista de apariciones justificadas y revisables.

## 4. Seguiran pasando los tests existentes?

No se puede garantizar sin ejecutarlos. Si entrenador_v2.py
permanece intacto y las dependencias que consume no cambian, la
migracion de etiquetado no deberia alterar su comportamiento
directamente.

Antes de migrar, congelaria los resultados de referencia de
chequeo1-3, auditoria, diagnosticos y tests de
convergencia/horizonte. Despues, los ejecutaria como regresion, sin
convertirlos en requisito de migracion contractual si no forman
parte de F0.

La salvedad es importante: si alguno consume bancos regenerados por
generar_banco_A2.py, si puede verse afectado indirectamente, aunque
el entrenador no haya cambiado.

Decision recomendada: F0 termina cuando el productor offline usa el
contrato canonico, preserva las etiquetas esperadas y tiene un
guardian acotado y verificable. Evaluador y runtime quedan
expresamente pendientes; no se modifican ni se declaran alineados
por anticipado.
