# ESTADO REAL DEL TIMONEL — 2026-10-10

**Autor:** Directora de Investigacion
**Estado:** foto real post-lectura completa de memos 57-66
**Reemplaza:** memo 70 (obsoleto, escrito con info parcial)

---

## 0. Por que este memo

El memo 70 fue escrito con informacion parcial (solo se leyeron las primeras
25 lineas de cada memo 57-66). Contenia errores de premisa que un hilo nuevo
de IA detecto. Este memo corrige.

**Leccion de metodo:** no escribir planes sin leer los documentos base
COMPLETOS. Las primeras 25 lineas no alcanzan. Los estados, los resultados
y las politicas suelen estar al final de los memos.

---

## 1. QUE YA ESTA RESUELTO (y el memo 70 no lo reflejaba)

### RUNTIME-CARRYOVER-001: CONFIRMED

Del memo 65 completo (no solo el encabezado):

> "RUNTIME-CARRYOVER-001: CONFIRMED"
> "Test 6: FAIL por diseño esperado" (el carry-over EXISTE)
> "Mecanismo exacto del carry-over: ABIERTO"
> "Accion inmediata: documentar y cerrar este capitulo"

**Que significa:** Ollama TIENE carry-over entre prompts consecutivos.
El resultado de un contexto fijo S* DEPENDE de los prompts anteriores.

**Politica operativa derivada:**

- **Benchmark con medicion limpia:** resetear el modelo entre casos
  (`ollama stop` y volver a cargar). Usar cuando el objetivo es comparar
  decisiones como si fueran independientes.
- **Benchmark de carry-over:** NO resetear. El estado heredado es el
  fenomeno que se mide.
- **Runtime operativo del agente:** NO resetear. El estado heredado es
  informacion legitima, no ruido.

### Mecanismo del carry-over: ABIERTO

No se sabe exactamente de donde viene (KV cache, estado del runner, u otro).
Esa investigacion queda separada. No bloquea el trabajo actual.

---

## 2. BLOQUEANTES REALES HOY (que el memo 70 no menciono)

### BLOQUEANTE 1 — Bug de Ollama con `format:json`

Del memo 66:

> "Ollama devolvio 5 de 6 respuestas vacias con el error."
> "Cualquier benchmark que dependa de format=json puede fallar
> silenciosamente."

**Fix pendiente:** sacar `format=json` de agente_llm.py y parsear
manualmente con regex. O buscar workaround.

**Impacto:** sin esto, ningun benchmark con Qwen es confiable.
Es BLOQUEANTE para cualquier etapa posterior.

### BLOQUEANTE 2 — Cambio de regimen de inferencia

Del memo 66:

> "Cambio de regimen de inferencia (NO RESUELTO)."

**Que significa:** durante un mismo benchmark, el comportamiento del
agente base cambia sin que uno lo haya cambiado. Eso invalida la
comparacion causal.

**Estado:** NO RESUELTO. Pero depende de BLOQUEANTE 1 (hay que
arreglar format:json antes de poder medirlo con confianza).

---

## 3. ESTADO REAL DEL TIMONEL

### Fases

- **Fase 1 (comandos fijos):** HECHA.
- **Fase 2 (piloto Python, `timon_python`):** EN USO.
  Ley de control matematica fija. NO aprende. NO tiene memoria.
- **Fase 3 (LLM decidiendo via Qwen):** CODIGO ESCRITO, NO CONECTADO.
  `consultar_dsh()` existe pero no se llama desde `main()`.

### Consecuencia

Hoy NO hay aprendizaje en sentido tecnico. Hay un pipeline armado
y funcionando con un piloto automatico matematico.

---

## 4. SIGUIENTE PASO UNICO (bloqueante)

**Arreglar el bug `format:json` en `agente_llm.py`.**

Sin eso:
- No se puede correr ningun benchmark con Qwen.
- No se puede verificar el cambio de regimen.
- No se puede conectar Qwen al main() de forma confiable.

**Como se hace:**
1. Abrir `timonel/agente_llm.py`.
2. Buscar donde usa `format: json` en el payload a Ollama.
3. Sacarlo.
4. Parsear la respuesta manualmente con regex (buscar el primer `{` y
   el ultimo `}`).
5. Verificar con un test corto: mismo prompt 20 veces, contar cuantas
   respuestas son parseables.

**Costo:** ~30 min.
**Riesgo:** bajo.

---

## 5. DESPUES DE ESO (orden bloqueante)

1. **Test de determinismo de Qwen** (con format:json ya arreglado).
2. **Conectar `consultar_dsh()` al `main()`** (Etapa 2 del memo 70 sigue valida).
3. **Benchmark H-NAV-001** (Qwen vs `timon_python`).
4. **Extender a velas** (requiere 3 aprobado).
5. **Memoria** (requiere 3 y 4 aprobados).

---

## 6. LO QUE NO SE HACE TODAVIA

- No correr benchmarks con Qwen (bug format:json).
- No extender el Timonel a velas.
- No meter presion a la mini PC.
- No escribir mas planes largos antes de leer los memos completos.

---

## 7. LECCION DE METODO (para futuros hilos)

**Error cometido:** escribir el memo 70 leyendo solo las primeras 25
lineas de cada memo 57-66. Eso hizo que:
- Se marcara como pendiente algo ya confirmado (H-CARRY-1).
- Se omitieran dos bloqueantes reales (format:json, cambio de regimen).
- Se escribieran preguntas redundantes a Luna/Claude.

**Regla nueva:** antes de escribir un plan que dependa de documentos
previos, LEERLOS COMPLETOS. Las primeras lineas no alcanzan. Los
estados y las politicas operativas suelen estar al final.

**Otra regla:** si el documento es muy largo, grep por palabras clave
("CONFIRMED", "PENDIENTE", "BLOQUEANTE", "RESUELTO", "ABIERTO") antes
de concluir el estado.

---

## 8. FIRMA

**Estado:** foto real.
**Proximo paso:** arreglar bug format:json.
**Bloqueantes activos:** 1 (format:json).
**Etapas posteriores:** definidas en memo 70 (siguen validas desde la
Etapa 2 en adelante).
