# NaveGo — Teoría Náutica y Cartografía de Referencia

Este archivo reúne los conceptos técnicos que guían el diseño de NaveGo.
No es un manual de navegación completo, sino una referencia interna para que
el equipo de desarrollo comprenda qué representan los datos que la app
muestra y cómo deben relacionarse entre sí.

---

## 1. Cartografía Náutica y Simbología

- **Sondas:** cifras métricas que indican profundidad.  
  Ejemplo: `29 St` = 29 metros con fondo de piedra.
- **Peligros:** naufragios, obstáculos, bajos, etc.  
  Se representan con símbolos específicos en la carta.
- **Balizamiento:** boyas, faros, torres y ayudas a la navegación.
- **Veriles o isobáticas:** líneas que unen puntos de igual profundidad.  
  Permiten identificar taludes y configuración batimétrica.

### Clasificación de cartas

- **Cartas generales:** navegación oceánica.
- **Cartas costeras:** recaladas y aproximación.
- **Cartuchos:** ampliaciones de puertos y pasos restringidos.

---

## 2. Publicaciones Náuticas Oficiales

- **Derroteros:** descripción de costas, peligros, corrientes y balizamiento.
- **Guías náuticas:** información práctica de puertos y servicios.
- **Libros de faros:** características lumínicas y señales de niebla.

---

## 3. Hidrografía y Sonda

- El transductor emite un pulso acústico hacia el lecho.
- La profundidad se calcula midiendo el tiempo de retorno del eco.
- La ecosonda muestra profundidad y densidad del fondo en tiempo real.

---

## 4. Magnetismo, Desvíos y Correcciones de Aguja

### Nortes y rumbos

| Símbolo | Significado |
|---|---|
| Nv | Norte verdadero / geográfico |
| Nm | Norte magnético |
| Na | Norte de aguja |
| Rv | Rumbo verdadero |
| Rm | Rumbo magnético |
| Ra | Rumbo de aguja |

### Corrección total
Aquí tenés el documento completo unificado, con toda la información desordenada del final estructurada con la misma jerarquía visual, títulos limpios, negritas y tablas formateadas en Markdown que el resto de la guía de referencia:

---

# NaveGo — Teoría Náutica y Cartografía de Referencia

Este archivo reúne los conceptos técnicos que guían el diseño de NaveGo. No es un manual de navegación completo, sino una referencia interna para que el equipo de desarrollo comprenda qué representan los datos que la app muestra y cómo deben relacionarse entre sí.

---

## 1. Cartografía Náutica y Simbología

* **Sondas:** cifras métricas que indican profundidad. Ejemplo: `29 St` = 29 metros con fondo de piedra.
* **Peligros:** naufragios, obstáculos, bajos, etc. Se representan con símbolos específicos en la carta.
* **Balizamiento:** boyas, faros, torres y ayudas a la navegación.
* **Veriles o isobáticas:** líneas que unen puntos de igual profundidad. Permiten identificar taludes y configuración batimétrica.

### Clasificación de cartas

* **Cartas generales:** navegación oceánica.
* **Cartas costeras:** recaladas y aproximación.
* **Cartuchos:** ampliaciones de puertos y pasos restringidos.

---

## 2. Publicaciones Náuticas Oficiales

* **Derroteros:** descripción de costas, peligros, corrientes y balizamiento.
* **Guías náuticas:** información práctica de puertos y servicios.
* **Libros de faros:** características lumínicas y señales de niebla.

---

## 3. Hidrografía y Sonda

* El transductor emite un pulso acústico hacia el lecho.
* La profundidad se calcula midiendo el tiempo de retorno del eco.
* La ecosonda muestra profundidad y densidad del fondo en tiempo real.

---

## 4. Magnetismo, Desvíos y Correcciones de Aguja

### Nortes y rumbos

| Símbolo | Significado |
| --- | --- |
| Nv | Norte verdadero / geográfico |
| Nm | Norte magnético |
| Na | Norte de aguja |
| Rv | Rumbo verdadero |
| Rm | Rumbo magnético |
| Ra | Rumbo de aguja |

### Corrección total

---

## 5. Análisis de la Carta Náutica para Navegación y Exámenes PER

### Resumen Ejecutivo

Este bloque sintetiza los conocimientos fundamentales para la interpretación y el uso de la carta náutica, centrándose específicamente en la carta del Estrecho de Gibraltar (estándar para exámenes de PER y Patrón de Yate). Permite posicionar la embarcación, planificar rutas seguras y ofrece datos críticos sobre batimetría, naturaleza del fondo, ayudas a la navegación y variaciones magnéticas.

### 5.1. Estructura Geográfica y Sistema de Coordenadas

La carta náutica se organiza con el Norte en la parte superior, el Sur en la inferior, el Este a la derecha y el Oeste a la izquierda.

* **Paralelos y Latitud:** Representan la latitud y se miden en los márgenes izquierdo y derecho (Escala de Latitudes). Destacan los paralelos 35° 50' N, 36° 00' N y 36° 10' N.
* **Meridianos y Longitud:** Representan la longitud y se encuentran en los márgenes superior e inferior (Escala de Longitudes). En el Estrecho se representan desde los 5° 20' W hasta los 6° 10' W.
* **Puntos de Referencia Clave:** Cabo Roche, Cabo de Trafalgar, puertos de Barbate, Algeciras, Ceuta, Tánger, y cabos estratégicos (Punta Europa, Isla de Tarifa, Cabo Espartel, entre otros).

### 5.2. Batimetría y Características del Fondo

La profundidad es un factor de seguridad crítico para evitar el encallamiento.

* **Medición de Profundidad (Sondas):** Las profundidades indicadas son las mínimas existentes, referenciadas a la "bajamar escorada" o mayor bajamar posible. Para obtener la sonda real, se suma la altura de la marea al valor de la carta.
* **Sistemas de Medición:** Aunque las cartas españolas usan metros, es vital comprender el sistema anglosajón para cartas internacionales:

| Unidad | Equivalencia en Metros | Notas |
| --- | --- | --- |
| **Braza (Fathom)** | 1.83 metros | Equivale a 6 pies. |
| **Pie (Foot)** | 0.305 metros | Un barco de 40 pies mide 12m. |

* **Veriles e Isobátas:** Líneas que unen puntos de igual profundidad. Código de colores de peligros:
* **Fondo Azul Claro:** Profundidades bajas (veriles de 10 y 20 metros). Requiere atención extrema.
* **Fondo Blanco:** Aguas más profundas (veriles de 30, 50, 100 y 200 metros).


* **Naturaleza del Fondo:** Fundamental para determinar la calidad del tenedero al fondear (representado con abreviaturas):
* **Arena:** Ideal para el fondeo.
* **Piedra / Cascajo:** Fragmentos de piedras o roca firme.



### 5.3. Ayudas a la Navegación: Faros y Balizas

Los faros se identifican mediante una estrella de cinco puntas con una "lágrima" de color rojo.

* **Interpretación de Códigos Lumínicos (Ritmo de la Luz):**
* **Destello (Fl):** La duración de la luz es menor que la de la oscuridad.
* **Ocultación (Oc):** La duración de la luz es más larga que la de la oscuridad.
* **Isofase (Iso):** Periodos de luz y oscuridad iguales.
* **Parámetros:** Número de destellos entre paréntesis, periodo total del ciclo en segundos (ej. 10s) y alcance visual en millas náuticas (M).


* **Casos de Estudio en el Estrecho:**
* **Faro de Punta Cirés:** `Fl(3) 10s 18M` (3 destellos, periodo de 10 segundos, alcance de 18 millas).
* **Faro de Punta Europa (Luz de Sectores):** Delimita zonas de seguridad mediante colores.
* **Luz Blanca (Iso W):** Sectores seguros; más intensa hacia mar abierto.
* **Luz Roja (Oc R):** Indica peligro (ej. riesgo de colisión con el Bajo de la Perla al aproximarse desde el Atlántico).




* **Marcas Cardinales (Boyas y Balizas):** Señalizan peligros o canales (ej. baliza del puerto de Tánger, Marca Cardinal Norte, identificable por dos triángulos hacia arriba).
* **Ritmos de Centelleo:** Centelleante Rápida (`VQ`, 80-160 destellos/min) y Centelleante (`Q`, 50-80 destellos/min).



### 5.4. Magnetismo Terrestre y Declinación

La declinación magnética ($dm$) es la diferencia angular entre el Norte Verdadero y el Norte Magnético.

* **La Rosa de Declinación:** Indica el valor de la declinación en un año específico y su variación anual debido al dinamismo del campo magnético terrestre.
* **Cálculo de Aplicación:**
* Si la declinación y la variación anual tienen el **mismo signo**, se suman.
* Si tienen **distinto signo**, se restan.


* **Ejemplo (Carta del Estrecho - Dato 2005):** Con una declinación de 2° 56' W y un decremento anual (variación hacia el Este), la declinación se reduce progresivamente acercándose al Norte Verdadero.