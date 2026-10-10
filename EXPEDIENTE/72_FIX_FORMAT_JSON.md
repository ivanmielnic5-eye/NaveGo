# FIX BUG format:json — Timonel

**Fecha:** 2026-10-10
**Autor:** Directora de Investigacion (hilo anterior)
**Estado:** CERRADO. Fix aplicado y verificado.
**Reemplaza parte del memo 71 (bloqueante 1).**

---

## 0. Proposito

Documentar el fix del bug format:json que bloqueaba cualquier
benchmark con Qwen. El memo 71 lo habia identificado como bloqueante 1.

---

## 1. QUE SE HIZO

### Identificacion: 2 archivos, no 1

El format:json estaba en DOS lugares:
- timonel/agente_llm.py linea 121 (consultar_qwen)
- timonel/timonel.py linea 127 (consultar_dsh)

El memo 66 solo mencionaba uno. Se encontraron los dos.

### Fix aplicado

Se saco la linea "format": "json" de ambos archivos.

Por que funciona: el parser manual _parsear_respuesta_json (en
agente_llm.py) YA EXISTIA y es robusto. Saca bloques markdown,
busca el primer { y el ultimo }, y parsea. Nunca dependio del
JSON nativo de Ollama.

### Backups creados

- timonel/agente_llm.py.pre-fix-formatjson-HHMM
- timonel/timonel.py.pre-fix-formatjson-HHMM
- timonel/timonel.py.pre-fix2-HHMM

---

## 2. TEST DE VERIFICACION

Script: /tmp/test_parseo.py
Modelo: qwen2.5-coder:1.5b
Consultas: 10 con el mismo prompt real.

Resultado: 10/10 respuestas parseables.
Todas: accion=corregir_rumbo, parametro=80

---

## 3. HALLAZGO SECUNDARIO: DETERMINISMO 1.5b

Las 10 respuestas fueron identicas con temperatura=0 y seed=555.

Conclusion: qwen2.5-coder:1.5b ES DETERMINISTA.

Falta verificar 3b y 7b con el mismo test.

---

## 4. MODELOS DISPONIBLES

- qwen2.5-coder:1.5b (986 MB) - tests rapidos
- qwen2.5-coder:3b (1.9 GB) - el que usa timonel.py hoy
- qwen2.5-coder:7b (4.7 GB) - pesado
- llama3.1:8b (4.9 GB) - alternativa

agente_llm.py usa 1.5b. timonel.py usa 3b. Los memos dicen 7b.
PENDIENTE: unificar criterio de que modelo usar cuando.

---

## 5. DOS MODOS DE TESTEO

### Modo A - Matematico puro (CPU, sin Godot)
- Corre solo. La IA lo ejecuta. No requiere presencia.
- Usa simulador_polaris.py.
- Ideal para: benchmarks grandes, 350 contextos.

### Modo B - Godot en vivo
- Requiere abrir Godot y tocar F5 manualmente.
- Usa fisica Jolt real, timon fisico, velas.
- Ideal para: validar fisica real, ver el barco.

### Guia de decision
- Qwen vs piloto Python -> Modo A.
- Decision del LLM en el barco -> Modo B.
- Memoria mejora decisiones -> Modo A.
- Fisica responde a viento + velas -> Modo B.

---

## 6. ESTADO FINAL

Bloqueante 1 (format:json): RESUELTO.
Bloqueante 2 (cambio de regimen): NO RESUELTO.
  Requiere el fix de format:json aplicado (ya esta), despues
  re-testear con el fix.

Proximo paso:
1. Verificar determinismo en 3b y 7b.
2. Conectar consultar_dsh() al main() de timonel.py.

---

## 7. REGLA DE METODO

Aprendizaje del memo 70: leer los memos completos, no solo los
encabezados. Los resultados, politicas y bloqueantes estan al
final de los documentos.

Corolario: usar grep por palabras clave (CONFIRMED, PENDIENTE,
BLOQUEANTE, RESUELTO, ABIERTO) antes de escribir un plan.

---

## 8. CIERRE DE HILO

Este memo cierra el hilo anterior. El hilo nuevo tiene el mando.
No hay doble escritor activo (R-INC-01 respetada).
