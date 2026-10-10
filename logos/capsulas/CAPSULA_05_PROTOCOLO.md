# 05 — Protocolo de trabajo (no negociable)

## Cómo se aplican los cambios
1. cp -v archivo archivo.pre-<etapa>   (backup explícito)
2. python3 heredoc con reemplazos exactos por string matching.
3. Cada reemplazo imprime [OK] n. <descripción> o [ERROR] n. <motivo>.
4. Al final: "Cambios aplicados: X/Y".
5. Verificación TypeScript filtrada por archivo, sin node_modules, sin backups/.

## Cómo se reporta
- Se pega la salida COMPLETA del bloque (OKs + ERRORs + tsc + Fin).
- No se resume. No se interpreta. La salida habla.
- Si algo falla, se restaura el backup y se re-aplica corregido.

## Qué NO se hace
- No meter dos pasos en un comando.
- No "aprovechar para limpiar" cosas no relacionadas.
- No avanzar sin confirmar salida del paso anterior.
- No confiar en memoria del chat: todo verificable contra disco.

## Test de aceptación por paso
- Todos los [OK] esperados presentes.
- 0 [ERROR].
- TypeScript: solo errores viejos preexistentes (ej: smoothedCog en App.tsx).

## Después de cada paso verificado
- Rebuild.
- Install.
- Test de replay comparando contra comportamiento previo.
