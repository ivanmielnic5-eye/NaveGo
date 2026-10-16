extends Node

@export var angulo_maximo : float = 45.0
@export var velocidad_giro : float = 60.0
@export var nombre_vela_mayor : String = "Vela_Mayor"
@export var nombre_foque : String = "Foque"
@export var eje : String = "z"

var _vela_mayor : Node3D = null
var _foque : Node3D = null
var _angulo_mayor : float = 0.0
var _angulo_foque : float = 0.0
var _rot_mayor_inicial : float = 0.0
var _rot_foque_inicial : float = 0.0

func _ready():
	await get_tree().process_frame
	var escena = get_tree().current_scene
	if escena == null:
		push_error("[Sail] No hay escena")
		return
	_vela_mayor = escena.find_child(nombre_vela_mayor, true, false)
	_foque = escena.find_child(nombre_foque, true, false)
	if _vela_mayor == null:
		push_error("[Sail] No se encontro: " + nombre_vela_mayor)
	else:
		print("[Sail] Vela_Mayor: ", _vela_mayor.get_path())
		_rot_mayor_inicial = _leer_rot(_vela_mayor)
	if _foque == null:
		push_error("[Sail] No se encontro: " + nombre_foque)
	else:
		print("[Sail] Foque: ", _foque.get_path())
		_rot_foque_inicial = _leer_rot(_foque)

func _leer_rot(obj):
	if eje == "z": return obj.rotation_degrees.z
	if eje == "y": return obj.rotation_degrees.y
	return obj.rotation_degrees.x

func _escribir_rot(obj, valor):
	if eje == "z": obj.rotation_degrees.z = valor
	elif eje == "y": obj.rotation_degrees.y = valor
	else: obj.rotation_degrees.x = valor

func _process(delta):
	var paso = velocidad_giro * delta

	# Vela Mayor: Q / E
	if _vela_mayor != null:
		var dir_m : float = 0.0
		if TestInput.pressed(KEY_Q): dir_m = 1.0
		if TestInput.pressed(KEY_E): dir_m = -1.0
		if abs(dir_m) > 0.01:
			_angulo_mayor += dir_m * paso
			_angulo_mayor = clamp(_angulo_mayor, -angulo_maximo, angulo_maximo)
		else:
			_angulo_mayor = move_toward(_angulo_mayor, 0.0, paso * 2.0)
		_escribir_rot(_vela_mayor, _rot_mayor_inicial + _angulo_mayor)

	# Foque: Z / X
	if _foque != null:
		var dir_f : float = 0.0
		if TestInput.pressed(KEY_Z): dir_f = 1.0
		if TestInput.pressed(KEY_X): dir_f = -1.0
		if abs(dir_f) > 0.01:
			_angulo_foque += dir_f * paso
			_angulo_foque = clamp(_angulo_foque, -angulo_maximo, angulo_maximo)
		else:
			_angulo_foque = move_toward(_angulo_foque, 0.0, paso * 2.0)
		_escribir_rot(_foque, _rot_foque_inicial + _angulo_foque)
