# Estrategia de Tipografía Adaptable — NaveGo

**Fecha:** 19 sep 2026
**Estado:** DISEÑO (no implementado todavía)
**Autor:** Director + IA técnica

---

## 1. Por qué importa

NaveGo no es una app de escritorio. Se usa en una embarcación:
- Con sol directo sobre la pantalla.
- Con las manos mojadas o con guantes.
- Con el celular en un soporte, a 60 cm de los ojos.
- Con usuarios de 20 a 70 años.
- Con o sin lentes puestos.
- En movimiento o en amarre.

El tamaño de letra no es un detalle estético: es usabilidad de campo.
Aplica igual para Logos (filosofía de interfaz todo terreno).

---

## 2. Estado actual (diagnóstico)

Los tamaños de letra viven dispersos:
- En theme.ts hay `fonts` con tamaños fijos.
- En cada archivo hay números sueltos (fontSize: 12, fontSize: 14).
- NO hay un lugar central desde donde se cambien todos.

Si el usuario quiere letra más grande, hoy hay que tocar código.

---

## 3. Estrategia en 4 capas (de adentro hacia afuera)

### Capa 1 — Tokens de tipografía
Crear "tamaños con nombre" en lugar de números sueltos.
Ej: texto_chico, texto_mediano, texto_grande.
Cambiar un token = cambia todo automáticamente.

### Capa 2 — Preferencia del usuario
Botón en Configuración → Texto con 3 opciones:
- Chico (0.9x)
- Mediano (1.0x) — actual
- Grande (1.3x)
El usuario elige, la app multiplica todos los tokens.

### Capa 3 — Persistencia
La elección se guarda en navego.db.
Reabre la app → ya está aplicada.
No vuelve a elegir cada vez.

### Capa 4 — Resiliencia
Si el texto crece mucho, los contenedores también crecen.
Botones se agrandan. Márgenes se ajustan.
Algunos elementos con ancho fijo van a necesitar revisión manual.

---

## 4. Impacto por capa

| Capa | Qué toca | Riesgo | Reversible |
|---|---|---|---|
| 1. Tokens | theme.ts + buscar fontSize sueltos | Bajo | Sí |
| 2. Preferencia | Agregar Config → Texto | Bajo | Sí |
| 3. Persistencia | Agregar tabla en navego.db | Muy bajo | Sí |
| 4. Resiliencia | Revisar contenedores fijos | Medio | Sí |

Ninguna capa rompe la arquitectura. Son adiciones, no refactors.

---

## 5. Plan escalonado (3 pasos, en orden)

### Paso A — Diagnóstico sin tocar código
Inventariar todos los fontSize sueltos.
Contarlos, ver dónde están.
NO se cambia nada. Solo la foto.

### Paso B — Centralizar tokens
Mover tamaños a theme.ts.
Reemplazar números sueltos por referencias.
Resultado: todo igual, pero un solo lugar para cambiar.

### Paso C — El multiplicador
Agregar factor de escala (0.9x / 1.0x / 1.3x).
Agregar botón Configuración.
Agregar persistencia.
Resultado: el usuario cambia tamaño y queda guardado.

No saltar pasos.

---

## 6. Lo que NO hacer todavía
- NO implementar Config antes de centralizar tokens.
- NO tocar el HUD landscape (donde se hizo REAL-01) hasta tener inventario.
- NO copiar el sistema a Logos hasta probarlo en NaveGo.

---

## 7. Dato a favor
React Native ya tiene sistema nativo de escalado (PixelRatio,
useWindowDimensions). No hay que inventar nada.

---

## 8. Decisiones del Director
- Prioridad: MEDIA (después de los bugs actuales).
- Orden: NaveGo primero, Logos después.
- Medición: el Director decide si se lee o no (sin formalismo).

---

## 9. VISIÓN DE FONDO (del Director, 19 sep 2026)

El propósito del sistema no es la tecnología. Es la experiencia del usuario.
La UX es la razón de ser de Logos y sus constelaciones.

Ejemplo concreto:
- Un usuario con vista cansada necesita letra más grande → accede.
- Un usuario ciego necesita audio/lector → también debería acceder.
- Un usuario mayor necesita contraste → también.
- Un usuario en un bote con guantes necesita botones grandes → también.

El sistema no es "software que funciona". Es "software que incluye".

Pregunta permanente en cada decisión de diseño:
"¿Quién queda afuera con esta elección?"

Logos como proyecto colectivo colaborativo: la interfaz es todo terreno
porque las personas son todo terreno. No hay un usuario "típico".
