# TRABAJO BLENDER — ESTADO AL 2026-10-09
# Sesion larga: elevacion de vela mayor, botavara, subdiv, foque, estay

## Archivo de trabajo

    /home/ivan/Descargas/sailboat_normalizado.blend

Backups:
    sailboat_normalizado.pre-renombres.blend
    sailboat_normalizado.pre-fase1.blend

## Que hay en la escena

Objetos MESH:
1. **Velero**   — casco + mastil + timon + jarcias. 3242 verts.
                  Contiene la barra del foque (soldada al mesh).
2. **Vela_Mayor** — 156 verts, 242 caras (subdividida).
                    rotation_mode QUATERNION, quat = (0.7071, -0.7071, 0, 0) = 90 X.
                    Origen en la amura: (-0.2669 -> 0.4569, -0.4195, 2.6710)
3. **Foque**    — 240 verts, 392 caras (subdividido).
                  rotation X = -1.5708, escala 0.0115.
                  Origen en la amura: (0.4620, 3.4522, 3.0044)
4. **Botavara** — 40 verts. Cilindro horizontal.
                  Diametro 12.6 cm. Largo 3.8434 m.
                  De y=-0.42 a y=-4.26 a z=2.671 (nivel pujamen).
5. **Estay_Foque** — 12 verts. Cable fino (radio 1.2 cm).
                  De tope del mastil (0.4844, -0.2717, 13.7598) a la amura del foque.

## Coordenadas clave

### Vela_Mayor (post elevacion 43 cm)
- Amura:  (0.4569, -0.4195,  2.6710)
- Escota: (0.4375, -4.2634,  2.6710)  <- enderezada a nivel amura
- Driza:  (0.4569, -0.4195, 13.7509)  <- a 0.89 cm del tope del mastil

### Foque
- Amura:  (0.4620, 3.4522,  3.0044)
- Escota: (0.4620, -0.2042, 2.8268)
- Driza:  (0.4620, -0.2672, 13.2176)

### Mastil
- Eje vertical en (x, y) ~ (0.46, -0.42)
- Diametro ~8.9 cm
- Tope en z = 13.7598

## Decisiones de diseno tomadas

1. **Vela_Mayor elevada 43 cm.** Pujamen sube a z=2.671, arriba de las barandillas.
   Driza a 0.89 cm del tope del mastil (margen minimo pero suficiente).
   Razon: liberar el pujamen para que la vela rote sin choques + look realista.

2. **Pujamen horizontal.** La escota se subio de z=2.207 a z=2.671 (mismo z que amura).
   Razon: botavara horizontal, look de velero cazado.

3. **Origen de Vela_Mayor en la amura.** Pivote en el gratil (amura->driza).
   Rotacion sobre ese eje = gira como puerta con bisagras en el mastil.
   Eje unitario: (0.0652, 0.0221, 0.9976).

4. **Botavara horizontal a z=2.671.** Diametro 12.6 cm (ajustado al mastil + 40%).
   Del mastil (y=-0.42) a la escota (y=-4.26). No hijo de la vela, giran juntos.

5. **Vela subdividida sin cambiar forma.** Vela_Mayor 6->156 verts, Foque 12->240.
   Necesario para Cloth o shader.

6. **Foque: origen en la amura (Y+3.45).** Pivote en su gratil inclinado 20 grados.
   Eje unitario: (0, -0.3422, 0.9396).

7. **Estay_Foque creado.** Cable visual del tope del mastil a la amura del foque.
   Sin el, el foque parece flotar.

8. **Cloth DESCARTADO para Godot.** Decision: usar shader (curvatura en GPU).
   Razon: soft body en Godot consume RAM, no escala con multiples barcos.
   El shader se curva segun viento, costo CPU ~0. Es lo que usan juegos de vela.

9. **Barra del foque: NO tocar.** Esta soldada al mesh Velero. Riesgoso separar.
   Si se quiere sacar en el futuro, hacer a mano en Edit Mode.

## Orientacion del modelo (CONFIRMADO 2026-10-09)

- Y POSITIVO = PROA (bow). Extremo angosto (2.9 cm ancho).
- Y NEGATIVO = POPA (stern). Extremo ancho (9.7 cm ancho).
- Mastil en Y=-0.42. Escota vela mayor en Y=-4.26 (popa). Amura foque en Y=+3.45 (proa).

## Que falta

1. **Timon.** Esta en Velero (soldado al casco). Medir, decidir si separar o rotar.
2. **Shader de viento en Godot.** Disenar en el motor, no en Blender.
3. **Export a Godot.** Ver memo 69 (.glb, no .blend).

## Reglas aprendidas (HARD RULES)

1. **NO guardar automaticamente** desde scripts Python via MCP.
   El guardado lo hace el Director con Ctrl+S cuando verifica visual.

2. **Backup del .blend** antes de cada serie de cambios.

3. **Un cambio por vez, con verificacion entre cada uno.**

4. **Los scripts del bridge (jsonl) van en el CHAT, no en bash.**

5. **Cuando algo se rompe: File -> Revert.** No Ctrl+Z.
   Python no crea paso de undo. Ctrl+Z post-script deja estados inconsistentes.

6. **Nunca obj.matrix_world = Matrix.Translation(...)** desde el bridge.
   Borra la rotacion natural. Si hay que transformar, PRE-multiplicar:
       obj.matrix_world = M_pivot @ M_rot @ obj.matrix_world

7. **Checks contra Fase 0, no contra identidad.**
   rotation_euler es stale cuando el modo es QUATERNION.

8. **Verificacion visual PRIMERO, numerica DESPUES.**
   Si hay conflicto, GANA LA VISTA.

9. **Medir vertices reales antes de mover origenes.**
   Fase 0 (solo lectura) obligatoria antes de cada cambio geometrico.

10. **Verificacion cruzada con Godot cuando haya dudas visuales.**

11. **No separar objetos soldados al mesh Velero con scripts.**
    Si hay que separar algo (barra del foque, timon), hacer a mano en Edit Mode.
    Los scripts con bmesh.separate pueden corromper el mesh.

12. **Confirmar Ctrl+S despues de cada fase antes de seguir.**
    Fases guardadas: elevacion vela mayor, pujamen horizontal, botavara, subdivision.
    Fase pendiente de confirmar: origen foque + estay.

13. **No empujar al Director a hacer cambios riesgosos por avanzar rapido.**
    El Director decide el ritmo. Los scripts son bajo su control.

## Referencias cruzadas

- Memo 68: Bridge Blender-MCP.
- Memo 69: Politica para actualizar el modelo en Godot via .glb.

---

## ACTUALIZACION 2026-10-09 (tarde) — TIMON

### Estado

- Timon separado del Velero como objeto independiente.
- Objeto: `Timon`, material gris claro (como el casco).
- Origen en el eje vertical (pivote correcto).
- Rota con R+Z en Blender (verificado visualmente por el Director).
- Guardado con Ctrl+S.

### Como se separo

1. Limpieza de objetos debug (marcadores, textos, DEBUG_Zona_Timon).
2. En Edit Mode sobre Velero: seleccion de verts con criterio `Y>3.5 AND Z<0.5`.
3. `mesh.separate(type='SELECTED')` -> nuevo objeto.
4. Renombrado a `Timon` + material gris claro.
5. Origen movido al eje vertical (centro X, centro Y, top Z del timon).

### Orientacion FINAL del modelo (DEFINITIVO)

- **Y POSITIVO = POPA (stern).** Confirmado con marcadores de texto: "Y=+5" cae sobre la popa.
- **Y NEGATIVO = PROA (bow).** Confirmado.
- Mastil en Y=-0.42.
- Amura del foque en Y=+3.45 -> el foque del modelo original esta en la POPA.
  **PENDIENTE:** decidir si se mueve a la proa (donde deberia estar en un velero real).
- Timon en Y~+5 (popa). Correcto.
- Botavara: del mastil (Y=-0.42) a la escota (Y=-4.26). Extiende hacia PROA.
  **ATENCION:** en un velero real, la botavara extiende hacia POPA.
  Con Y+=popa, la botavara del modelo apunta al lado opuesto.
  Revisar si el modelo original tiene la botavara al reves o si es decision de diseño.

### Lecciones aprendidas en esta sesion

- **NO confiar en la intuicion de orientacion del asistente.** Usar marcadores visuales (texto 3D).
- **PCA falla con velas y jarcias.** El calculo de ancho captura la vela mayor y da resultados absurdos (13 m de ancho en un barco de 3 m). NO usar PCA para esto.
- **Confirmar siempre la orientacion con el Director** antes de mover origenes o crear geometria.

### Que falta

1. **Revisar la botavara** — puede estar apuntando al lado opuesto (proa en vez de popa).
2. **Revisar el foque** — puede estar ubicado en la popa (mal) en vez de la proa.
3. **Rotacion del timon** — test formal con scripts para confirmar el eje.
4. **Shader de viento en Godot** — diseñar en el motor.
5. **Export a Godot** — via .glb (memo 69).

---

## PLAN SHADER VIENTO — para próxima sesión (2026-10-11)

### Diagnostico GLB (2026-10-10 01:40)

- Vela_Mayor: 156 verts, 726 indices, CON UVs (TEXCOORD_0). OK.
- Foque: 240 verts, 1176 indices, SIN UVs. Se calcula por posicion.
- Estay_Foque, Timon, Velero, Soga_Foque, Botavara: con UVs.

### Plan

1. Crear `sail_wind.gdshader`:
   - Shader spatial.
   - Uniform: `wind_pressure` (float 0..1).
   - Uniform: `direccion_viento` (vec3).
   - Calculo: bulge = sin(distancia_normalizada_al_centro * PI) * wind_pressure.
   - Aplicar desplazamiento en direccion de NORMAL o perpendicular al plano.
   - Bordes (amura, escota, driza) = 0 bulging (quedan fijos).

2. Crear `sail_visual.gd`:
   - Busca MeshInstance3D de Vela_Mayor y Foque.
   - Asigna el shader (ShaderMaterial + el .gdshader).
   - Cada frame: calcula presion efectiva = factor_viento * eficiencia_vela.
   - Setea `material.set_shader_parameter("wind_pressure", presion)`.

3. Agregar nodo `SailVisual` en `main.tscn`.

4. Probar: viento fuerte + velas abiertas -> vela inflada. Viento debil o velas rectas -> vela plana.

### Referencias utiles

- La vela es un triangulo plano. El centro geometrico = promedio de los 3 vertices esquina (amura, escota, driza).
- Para saber si un vert esta en el borde: distancia al segmento mas cercano (grátil/baluma/pujamen) < umbral.
- Alternativa: usar `sqrt(uv.x * (1-uv.x) * uv.y * (1-uv.y))` si tiene UVs (Vela_Mayor).

### Comando de arranque del hilo nuevo

~/.logos/bin/logos-arranque
