# Reservorio de Modelos IA — NaveGo

Registro de modelos evaluados para posible uso futuro.
Regla: consultar aca ANTES de integrar cualquier IA nueva.

---

## [2026-09-21] Jev (JEP) — Type Save

**Veredicto:** NO para NaveGo hoy. Reevaluar cuando existan comandos por voz.

**Que es:**
- Modelo de clasificacion (devuelve etiquetas, no texto largo).
- Funciona como un "if" o "switch case" inteligente.
- Consume muy pocos tokens (menos de 500 por consulta).

**Pros:**
- Barato y rapido.
- Respuestas estructuradas.

**Contras:**
- REQUIERE INTERNET (API HTTP). Rompe la independencia offline de NaveGo.
- Latencia (~1s por respuesta).
- No resuelve ningun problema actual de NaveGo.

**Cuando podria tener sentido:**
- Comandos por voz.
- Ruteo inteligente con criterios no programables.

**Cuando NO:**
- Para bugs que se resuelven con reglas simples.
- Para nada que NaveGo necesite offline.

---

## Plantilla para futuras evaluaciones

### [FECHA] Nombre — Empresa

**Veredicto:** SI / NO / FUTURO
**Que es:**
**Pros:**
**Contras:**
**Cuando podria tener sentido:**
**Cuando NO:**
