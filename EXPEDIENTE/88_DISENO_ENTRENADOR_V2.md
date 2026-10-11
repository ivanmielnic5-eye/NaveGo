# DISENO DEL ENTRENADOR v2 — Continuacion comun

**Fecha:** 2026-10-11
**Autor:** Directora de Investigacion + Director
**Estado:** PROPUESTA. Pendiente de implementar.
**Complementa:** memos 86, 87.

---

## 0. Proposito

Disenar el Entrenador v2 corrigiendo el bug del v1 (comparacion injusta
entre recetas de duraciones distintas). Este memo define el diseno ANTES
de tocar codigo.

---

## 1. EL BUG DEL v1

En _simular_receta, cada receta corre hasta que TERMINA o hasta timeout.
Pero las recetas tienen duraciones efectivas distintas:

- corregir_rumbo: termina cuando el barco esta alineado (~10-20s).
- ir_a_punto: termina cuando llega (o timeout = horizonte completo).
- frenar: termina cuando el barco esta lento (~30s).

Medir "distancia final" al horizonte favorece a las recetas mas largas.
El "67% de error" del memo 86 era artefacto de este bug.

---

## 2. PRINCIPIO DE DISENO — OPCION D

> Cada receta corre TODO EL HORIZONTE sin "terminar".
> Nunca se detiene por alineacion, llegada o velocidad objetivo.
> Lo que cambia entre recetas es el TIPO de maniobra, no la duracion.

Esto elimina la nocion de "terminar antes" y hace las comparaciones
100% justas por diseno.

---

## 3. DISENO DE LAS 4 RECETAS EN v2

### corregir_rumbo_v2(b, meta_x, meta_z, horizonte_s)
- A cada ciclo: calcula rumbo hacia meta.
- Aplica timon para reducir el delta.
- Avance=1 siempre (para tener prop wash).
- NO TERMINA hasta el horizonte, aunque el delta sea 0.
- Si el delta es 0, mantiene timon=0 y avance=1.

### ir_a_punto_v2(b, meta_x, meta_z, horizonte_s)
- A cada ciclo: calcula rumbo hacia meta.
- Aplica timon proporcional al delta.
- Avance=1 siempre.
- NO TERMINA hasta el horizonte, aunque llegue a la meta.
- Si llega: sigue navegando hacia la meta (ya esta ahi, no hace dano).

### frenar_v2(b, horizonte_s)
- A cada ciclo: reduce velocidad a ~0.3 kn.
- NO TERMINA hasta el horizonte.
- Una vez en 0.3 kn, mantiene la velocidad objetivo.

### terminar_v2(b, meta_x, meta_z, horizonte_s)
- Sigue siendo accion logica. No hace maniobra fisica.
- Se evalua como "mision completa si dist < 15m".
- Su progreso se calcula igual que las otras: distancia al horizonte.

---

## 4. CAMBIO EN LA INTERFAZ

Las recetas dejan de tener timeout_s y reciben horizonte_s.

Firma v1:  corregir_rumbo(b, objetivo_deg, tol_deg=8, timeout_s=60)
Firma v2:  corregir_rumbo_v2(b, objetivo_deg, horizonte_s)

Las recetas v1 se mantienen para no romper otros usos.
Las v2 se agregan al lado.

---

## 5. IMPLEMENTACION

Archivo nuevo: `recetas_navegacion_v2.py`.
- Las 4 recetas v2.
- Test: cada una corre exactamente horizonte_s.
- Test: comparables entre si.

Entrenador v2: `entrenador_v2.py`.
- Hereda de Entrenador pero usa las recetas v2.
- Mantiene el resto de la logica (progreso trapezoidal, boundary, etc.).
- Las metricas son comparables ahora.

---

## 6. PROXIMOS PASOS

1. Implementar recetas_navegacion_v2.py.
2. Tests unitarios de las 4 recetas (duracion exacta = horizonte).
3. Implementar entrenador_v2.py.
4. Re-correr los tests de convergencia con v2.
5. Comparar v1 vs v2 sobre los mismos 300 contextos.
6. Documentar diferencias.

---

## 7. LO QUE NO SE HACE TODAVIA

- NO se re-etiqueta el banco CC002.
- NO se re-entrena el SFT.
- NO se toca el confirmatorio.
- NO se cambia el horizonte todavia (se decide despues).

---

## 8. FIRMA

**Estado:** PROPUESTA.
**Proximo paso:** implementar recetas_navegacion_v2.py.
**Regla del Director:** calidad primero, performance despues.
