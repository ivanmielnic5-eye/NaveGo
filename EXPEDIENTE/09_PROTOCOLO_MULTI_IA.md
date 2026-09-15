
## PROTOCOLO DE AISLAMIENTO POR DESCONEXIÓN (Modo Soberano)

Definición:
Cuando el celular está desconectado físicamente de la PC
(USB desconectado + terminal de Metro cerrada), el sistema
de navegación corre en Modo Soberano. La PC no puede
modificar la app del celular.

Fundamento técnico:
El APK release lleva el bundle JS empaquetado adentro.
No descarga código de la PC al abrir. Sin USB ni terminal,
no hay canal de modificación.

Aplicación:
- Modo Desarrollo: USB conectado + Metro corriendo.
  Para desarrollar.
- Modo Soberano: USB desconectado + Metro cerrado.
  Para navegar de verdad.

Verificación pendiente:
- Confirmar que la app no expone puertos de red.
- Documentar cómo se garantiza el aislamiento total.

Regla:
Un sistema es soberano cuando el usuario puede elegir cuándo
está conectado y cuándo no, y cuando la desconexión garantiza
que nadie externo puede modificarlo.

## PROTOCOLO — Verificación de Modo Soberano antes de elaborar scripts

Regla: antes de empezar cualquier sesión de trabajo sobre código
que pueda afectar al celular, se verifica que el celular esté
en Modo Soberano (aislado).

Comando de verificación:
echo "=== VERIFICACIÓN DE AISLAMIENTO ==="; echo ""; echo "1. Dispositivos ADB conectados:"; adb devices | tail -n +2; echo ""; echo "2. Metro/Expo corriendo:"; pgrep -f "expo start\|metro" || echo "   (ninguno)"; echo ""; echo "3. Puerto 8081 escuchando:"; ss -tlnp 2>/dev/null | grep 8081 || echo "   (puerto libre)"; echo ""; echo "=== FIN VERIFICACIÓN ==="

Interpretación:
- ADB vacío + Metro "(ninguno)" + Puerto 8081 libre
  -> Modo Soberano activo. Seguro para elaborar.
- Cualquier otro caso -> Modo Desarrollo.
  Aviso: cambios en código pueden afectar el celular en vivo.

Ciclo:
1. Antes de elaborar: verificar aislamiento.
2. Elaborar: editar archivos, probar localmente.
3. Terminar: reconectar USB, arrancar Metro.
4. Aplicar: npx expo run:android --variant release.
5. Volver a aislar: desconectar USB + cerrar terminal.
