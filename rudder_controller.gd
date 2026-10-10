extends Node

@export var angulo_maximo : float = 35.0
@export var velocidad_giro : float = 60.0
@export var nombre_timon : String = "Timon"
@export var torque_max : float = 5500.0
@export var velocidad_min_efecto : float = 0.5
@export var invertir : bool = false

var _timon : Node3D = null
var _sailboat : RigidBody3D = null
var _angulo_actual : float = 0.0
var _rotacion_inicial_z : float = 0.0

func _ready():
	await get_tree().process_frame
	var escena = get_tree().current_scene
	if escena == null:
		push_error("[Rudder] No hay escena")
		return
	_timon = escena.find_child(nombre_timon, true, false)
	if _timon == null:
		push_error("[Rudder] No se encontro: " + nombre_timon)
		return
	print("[Rudder] Timon encontrado: ", _timon.get_path())
	_rotacion_inicial_z = _timon.rotation_degrees.z

	_sailboat = escena.find_child("SailboatBody", true, false) as RigidBody3D
	if _sailboat == null:
		push_warning("[Rudder] SailboatBody no encontrado. Sin fisica.")
	else:
		print("[Rudder] SailboatBody: ", _sailboat.get_path())

func _process(delta):
	if _timon == null:
		return
	var direccion : float = 0.0
	if Input.is_key_pressed(KEY_A):
		direccion = 1.0
	if Input.is_key_pressed(KEY_D):
		direccion = -1.0
	if invertir:
		direccion = -direccion
	
	if abs(direccion) > 0.01:
		_angulo_actual += direccion * velocidad_giro * delta
		_angulo_actual = clamp(_angulo_actual, -angulo_maximo, angulo_maximo)
	else:
		_angulo_actual = move_toward(_angulo_actual, 0.0, velocidad_giro * delta * 2.0)
	
	_timon.rotation_degrees.z = _rotacion_inicial_z + _angulo_actual

func _physics_process(_delta):
	if _sailboat == null:
		return
	var fraccion : float = _angulo_actual / angulo_maximo
	if abs(fraccion) < 0.01:
		return
	var vel = _sailboat.linear_velocity
	var speed = Vector2(vel.x, vel.z).length()
	var eficiencia : float = clamp(speed / velocidad_min_efecto, 0.0, 1.0)
	var torque : float = fraccion * torque_max * eficiencia
	_sailboat.apply_torque(Vector3.UP * torque)
