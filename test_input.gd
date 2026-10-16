extends Node

# ============================================================
# TEST INPUT — Autoload para inyección de comandos en headless
# ============================================================
# Los scripts de control consultan a este nodo en lugar de (o además de)
# Input.is_key_pressed. En modo test, las teclas se activan/desactivan
# programáticamente desde el runner.
#
# Uso:
#   TestInput.set_active(KEY_W, true)
#   TestInput.is_active(KEY_W)  -> true
#   TestInput.clear()

var _teclas_activas: Dictionary = {}
var _test_mode: bool = false

func set_test_mode(activo: bool) -> void:
	_test_mode = activo
	if not activo:
		_teclas_activas.clear()

func is_test_mode() -> bool:
	return _test_mode

func set_active(keycode: int, activo: bool) -> void:
	if activo:
		_teclas_activas[keycode] = true
	else:
		_teclas_activas.erase(keycode)

func is_active(keycode: int) -> bool:
	return _teclas_activas.get(keycode, false)

func clear() -> void:
	_teclas_activas.clear()

# Helper combinado: teclado real o test
func pressed(keycode: int) -> bool:
	if _test_mode:
		return is_active(keycode)
	return Input.is_key_pressed(keycode)
