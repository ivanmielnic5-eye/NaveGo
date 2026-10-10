# PROPUESTA DE INVESTIGACION — Timonel, Carry-Over y Navegacion Asistida

> **OBSOLETO — 2026-10-10 14:15**
>
> Este memo fue escrito con informacion PARCIAL: solo se leyeron las
> primeras 25 lineas de cada memo 57-66. Consecuencias:
> - La Etapa 0 (H-CARRY-1) figura como pendiente, pero el memo 65
>   completo dice "RUNTIME-CARRYOVER-001: CONFIRMED". Ya fue ejecutada.
> - No menciona el bug `format:json` de Ollama (memo 66, problema 1).
> - No menciona el cambio de regimen de inferencia (memo 66, problema 2).
> - Las preguntas a Luna/Claude son parcialmente redundantes: los memos
>   63, 64 y 65 ya responden varias.
>
> Reemplazado por el memo 71 (foto real).
> Se conserva como registro historico y por la leccion de metodo.
>
> ---
>
> 
**Fecha:** 2026-10-10
**Autor:** Directora de Investigacion (asistida)
**Estado:** BORRADOR para consulta externa (Luna GPT + Claude) antes de ejecutar
**Alcance:** definir el orden bloqueante de investigacion y las hipotesis falsables

---

## 0. Proposito

Antes de tocar codigo en el Timonel, queremos:

1. Aclarar el estado REAL del sistema (que hoy NO aprende, solo ejecuta).
2. Definir el orden bloqueante de las etapas.
3. Que la comunidad de IAs (Luna + Claude) critique el plan antes de ejecutarlo.
4. Ejecutar H-CARRY-1 (rapida, bloqueante).

---

## 1. ESTADO REAL DEL TIMONEL (aclaracion importante)

Timonel hoy tiene 3 fases definidas (memo 57). Estado:

- **Fase 1 (comandos fijos):** HECHA. El Timonel escribe timon=0 fijo. Es un test de que el pipeline funciona.
- **Fase 2 (piloto Python, timon_python):** EN USO. Es una ley de control matematica fija:
    si delta > 15 grados, gira; si no, avanza. No aprende. No tiene memoria.
    Es un termostato, no un aprendiz.
- **Fase 3 (LLM decidiendo via Qwen):** CODIGO ESCRITO, NO CONECTADO.
    La funcion consultar_dsh() existe en timonel.py pero no se llama.

**Consecuencia:** hoy NO hay aprendizaje en sentido tecnico. Lo que hay
es un pipeline armado y funcionando.

---

## 2. ORDEN BLOQUEANTE DE ETAPAS

Cada etapa se apoya en la anterior. Si se saltea una, las de arriba son ruido.

### ETAPA 0 — H-CARRY-1 (bloqueante, ~15 min)

**Que:** determinar si Ollama tiene carry-over entre prompts consecutivos.

**Por que primero:** el memo 64 documento que el benchmark de memoria
(memo 62) quedo invalidado porque el runtime cambio de regimen durante la
ejecucion. Si Ollama "arrastra" estado entre prompts, todo benchmark causal
es interpretable de mil formas.

**Protocolo:** ya cerrado en memo 65. Ver seccion 3 abajo.

**Costo:** bajo. Poquitos prompts. No consume la mini PC.

### ETAPA 1 — Determinismo de Qwen (~20 min)

**Que:** verificar si Qwen da respuestas identicas al mismo input
(temperatura=0, seed fijo) en N repeticiones.

**Por que:** si no es determinista, no hay reproducibilidad. Sin
reproducibilidad no hay test.

**Protocolo:** a definir. Simple: mismo prompt 20 veces, comparar salidas.

### ETAPA 2 — Conectar Qwen al main() (Fase 3 pura, ~15 min)

**Que:** cambiar timon_python() por consultar_dsh() en timonel.py.
Solo timon, sin velas.

**Por que:** validar que el pipeline LLM->comando->fisica funciona
end-to-end.

**Metrica:** que el barco se mueva, que las decisiones lleguen, que no
crashee.

### ETAPA 3 — Benchmark H-NAV-001 (~1 hora)

**Hipotesis H-NAV-001:** Qwen decide timon igual o mejor que el piloto
Python simple en misiones multi-meta.

**Metrica:** regret vs oraculo (ya definido en memo 61).

**Baseline:** timon_python (Fase 2).

**Contexto:** COMMON_CONTEXT-001 (350 contextos congelados, memo 62).

**Criterio de falsacion:** si Qwen tiene regret mayor O tasa de exito
menor que timon_python, H-NAV-001 se refuta.

### ETAPA 4 — Extender a velas (~2 horas)

**Hipotesis H-NAV-002:** agregar control de velas al Timonel mejora la
tasa de exito sobre solo timon.

**Requiere:** ETAPA 3 aprobada.

### ETAPA 5 — Memoria (~2-3 horas)

**Hipotesis H-MEM-001:** la memoria externa mejora las decisiones del
Timonel sobre no-memoria.

**Requiere:** ETAPA 3 y 4 aprobadas. Y H-CARRY-1 y H-DETERM resueltas.

---

## 3. H-CARRY-1 EN DETALLE (copiada del memo 65, resumida)

### Hipotesis
- **H-CARRY-1:** la salida de un contexto fijo S* depende de los prompts
  ejecutados inmediatamente antes.
- **H-CARRY-0 (alternativa):** la salida de S* es independiente del prompt
  previo.

### Criterio de falsacion
Si para todas las precondiciones probadas la salida de S* es identica,
H-CARRY-1 se refuta.

### Definiciones operativas
- **S* (contexto sentinela):** contexto fijo, siempre el mismo input.
  Definido en memo 65 seccion 2.

### Diseno (a confirmar ejecutando memo 65)
1. Definir S*.
2. Ejecutar S* despues de distintos prompts previos (P1, P2, ..., Pn).
3. Comparar la salida de S* en cada caso.
4. Si todas las salidas son identicas -> H-CARRY-0 confirmada.
5. Si alguna difiere -> H-CARRY-1 confirmada.

### Costo
Bajo. ~10-20 prompts. No consume recursos significativos.

---

## 4. PEDIDO A LUNA Y CLAUDE

**No pedimos que disenen desde cero.** Pedimos critica de este plan.

### Preguntas concretas

1. **Sobre el orden:** las 6 etapas estan correctamente ordenadas como
   bloqueantes? Falta alguna etapa? Sobra alguna?

2. **Sobre H-CARRY-1:** el diseno del experimento es correcto? Se nos
   escapa algun confusor? Hay una manera mas limpia de testear carry-over
   en un runtime de LLM local?

3. **Sobre la aclaracion del "no aprende":** es correcto decir que el
   sistema hoy NO aprende? O hay algun sentido tecnico en el que el
   piloto Python con memoria externa (memo 60) ya constituye aprendizaje?

4. **Sobre las metricas:** regret vs oraculo (memo 61) es la metrica
   correcta? O sugeris otra?

5. **Sobre riesgos:** que riesgos ves en este plan? Que podria fallar?

### Formato de respuesta esperado
- Punto por punto.
- Se puede discrepar en todo.
- Si algo no aplica, decirlo.
- No inventar datos.

---

## 5. LO QUE NO SE HACE HOY

- No se corre el benchmark completo de memoria (350 contextos).
- No se extiende el Timonel a velas.
- No se mete presion a la mini PC.
- No se toca el codigo hasta que el plan este aprobado por el Director
  y (opcionalmente) comentado por Luna y Claude.

---

## 6. FIRMA

**Estado:** BORRADOR. Pendiente:
1. Revision del Director.
2. Consulta a Luna GPT.
3. Consulta a Claude.
4. Aprobacion final.
5. Ejecucion de H-CARRY-1.

**Regla:** ningun experimento se ejecuta sin hipotesis falsable escrita
ANTES. Este documento es esa hipotesis.
