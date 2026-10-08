# MANUAL DE ARRANQUE DE HILO NUEVO

Ultima actualizacion: 2026-10-08
Proposito: rutina canonica para arrancar un hilo nuevo sobre NAVEGO
o sobre el simulador Godot, sin perder contexto.

---

## FLUJO PRINCIPAL (un solo comando)

    cd ~/navego_recuperado && ./.logos/bin/logos-arranque

Hace todo automaticamente:
  1. Verifica el gate.
  2. Regenera el brief de NAVEGO.
  3. Compone CONTEXTO_ARRANQUE_NAVEGO.txt en el Escritorio.
  4. Lo copia al portapapeles (requiere wl-clipboard o xclip).
  5. Solo queda pegar en el chat del hilo nuevo con Ctrl+V.

Si el portapapeles no esta disponible, el archivo queda igual en
~/Escritorio/CONTEXTO_ARRANQUE_NAVEGO.txt.

Si el gate esta BLOCKED en el momento de correrlo, el archivo se
genera igual, pero la seccion 2 va a mostrar el bloqueo. En ese
caso, no trabajar hasta resolverlo.

Esta rutina (las secciones siguientes) es el detalle manual por
si logos-arranque falla o para entender que hace por dentro.

---

## Por que existe este documento

Cuando un hilo de IA se llena o se corta, se pierde el contexto. Este
manual es la rutina probada para que un hilo nuevo arranque con todo
lo necesario sin que el Director tenga que explicarlo todo a mano.

---

## Rutina de arranque (NAVEGO)

### Paso 1 - Abrir terminal

Al abrir terminal, `logos-context` corre solo y muestra un recuadro
con el estado del proyecto. Leerlo:
- Proyecto: NAVEGO
- Estado: OPERATIVO / BLOQUEADO / etc.
- Riesgo: verde / amarillo / rojo
- Hipotesis activa
- Proximo paso

### Paso 2 - Verificar el gate

    cd ~/navego_recuperado
    ./.logos/bin/logos-gate NAVEGO

- READY: todo bien, seguir.
- WARNING: hay algo leve, seguir pero anotar.
- BLOCKED: algo cambio y no esta revisado. PARAR y avisar al Director.

### Paso 3 - Regenerar el brief

    ./.logos/bin/logos-brief NAVEGO

Genera:
- EXPEDIENTE/BRIEF_NAVEGO.md           (version lectura)
- EXPEDIENTE/BRIEF_NAVEGO_pegable.txt  (version para pegar en chat)

### Paso 4 - Pegar el brief en el hilo nuevo

    cat EXPEDIENTE/BRIEF_NAVEGO_pegable.txt

Copiar todo y pegar en el chat del hilo nuevo (DeepSeek, Luna, GPT,
Claude, el que sea). Eso le da el contexto completo.

---

## Rutina de arranque (Simulador Godot)

Si el hilo nuevo es sobre el simulador, usar:

    ~/.logos/bin/logos-open simulador

Eso abre una terminal nueva con:
- El gate ya verificado.
- El brief regenerado.
- La seccion 10 (Simulador Godot) ya visible.

Dentro de esa terminal, pegar la seccion del simulador en el chat.

---

## Rutina durante el trabajo

### Antes de tocar codigo importante
- Ver el brief (paso 3).
- Mirar el gate (paso 2).

### Despues de tocar una fuente del MANIFEST
Si se modifico una fuente declarada en el MANIFEST.json, hay que
actualizar su hash:

    ./.logos/bin/logos-hash --verbose <path de la fuente>

El comando imprime el hash actual. Copiarlo al MANIFEST.json en el
campo `reviewed_against_hash` de la fuente correspondiente.

Sin esto, el gate va a marcar la fuente como STALE.

### Al cerrar la sesion
- git add de lo que cambio.
- git commit con mensaje claro y descriptivo.
- git push.

Formato de mensaje de commit:
- Linea 1: resumen corto (max 72 chars).
- Linea 2 en blanco.
- Cuerpo: que cambio y por que. Una linea por cambio relevante.
- Al final: refs a decisiones (D-2026-NNNN) o expedientes.

---

## Reglas duras

1. NO inventar comandos. Si no se sabe, preguntar.
2. NO forzar commit con -f. Si git se queja, hay un motivo.
3. NO mezclar cambios no relacionados en el mismo commit.
4. NO actualizar el hash de una fuente sin revisar el contenido.
   Seria "mentir" al sistema.
5. NO abrir dos hilos trabajando en el mismo archivo al mismo tiempo.
   Regla R-INC-01.
6. Backup explicito .pre-<etapa> antes de tocar codigo critico.
7. Los .pre-* de backup NUNCA se borran sin permiso del Director.

---

## Comandos clave (referencia rapida)

Gate:
    ./.logos/bin/logos-gate NAVEGO
    ./.logos/bin/logos-gate NAVEGO --json

Brief:
    ./.logos/bin/logos-brief NAVEGO

Hash de una fuente:
    ./.logos/bin/logos-hash <path>
    ./.logos/bin/logos-hash --full <path>
    ./.logos/bin/logos-hash --verbose <path>

Capsula de memoria:
    ./.logos/bin/logos-mem NAVEGO

Modo simulador:
    ~/.logos/bin/logos-open simulador

Contexto:
    ~/.logos/bin/logos-context --level=4

---

## Estados del gate (D-2026-0009 + D-2026-0010)

CURRENT:     el contenido actual coincide con el hash revisado.
STALE:       el contenido cambio despues del review.
DIVERGED:    (solo fuentes con commit) el review no es ancestro de HEAD.
INVALID:     el review apunta a algo inexistente.
UNREVIEWED:  nunca se reviso.

Politica:
- CURRENT -> OK
- STALE + optional -> WARNING
- STALE + required -> BLOCKED
- UNREVIEWED + optional -> WARNING
- UNREVIEWED + required -> BLOCKED
- DIVERGED -> BLOCKED siempre
- INVALID -> BLOCKED siempre

---

## Que NO hacer

- No crear fuentes nuevas en el MANIFEST sin hashearlas y agregarlas
  a la lista required u optional.
- No asumir que el gate esta OK sin correrlo.
- No trabajar sobre el simulador sin antes verificar que
  simulator_source esta CURRENT.
- No actualizar reviewed_against_commit como mecanismo de freshness
  (fue reemplazado por reviewed_against_hash en D-2026-0010).
