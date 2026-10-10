extends Node3D

@export var target_path: NodePath
@export var sail_controller_path: NodePath

@export_group("Intensidad del Viento")
@export var wind_speed_ms: float = 20.0
@export_range(0.0, 50.0, 0.5) var wind_strength: float = 0.3
@export_range(0.0, 10.0, 0.1) var gust_amplitude: float = 0.5
@export_range(0.0, 5.0, 0.1) var gust_frequency: float = 1.5

@export_group("Direccion del Viento")
@export_range(0.0, 360.0, 1.0) var wind_direction_deg: float = 0.0
@export_range(0.0, 5.0, 0.1) var direction_variation: float = 0.3

@export_group("Velas")
@export var vela_mayor_peso: float = 1.0
@export var foque_peso: float = 0.5
@export var eficiencia_minima: float = 0.1

@export_group("Debug")
@export var debug_print: bool = true

var target: RigidBody3D
var sail_controller: Node = null
var time: float = 0.0

func _ready() -> void:
	target = get_node_or_null(target_path) as RigidBody3D
	if target == null:
		push_warning("[Wind] Target no encontrado.")
	else:
		print("[Wind] Target: ", target.name)

	if sail_controller_path:
		sail_controller = get_node_or_null(sail_controller_path)
	if sail_controller == null:
		var raiz = get_tree().current_scene
		if raiz:
			sail_controller = raiz.find_child("SailController", true, false)
	if sail_controller:
		print("[Wind] SailController conectado: ", sail_controller.get_path())
	else:
		print("[Wind] SailController NO encontrado. Viento constante.")

func _physics_process(delta: float) -> void:
	if target == null:
		return
	time += delta

	var gust = sin(time * gust_frequency) * gust_amplitude
	var strength_now = wind_strength * 1000.0 + gust * 100.0

	var dir_offset = sin(time * direction_variation) * 15.0
	var angle_rad = deg_to_rad(wind_direction_deg + dir_offset)
	var wind_direction = Vector3(sin(angle_rad), 0.0, cos(angle_rad)).normalized()

	# --- Factor por las velas ---
	var factor : float = 1.0
	if sail_controller != null:
		var ang_mayor = sail_controller.get("_angulo_mayor")
		var ang_foque = sail_controller.get("_angulo_foque")
		if ang_mayor == null: ang_mayor = 0.0
		if ang_foque == null: ang_foque = 0.0

		var b = target.global_transform.basis
		var forward : Vector3 = -b.z
		var right : Vector3 = b.x
		var w_fwd : float = wind_direction.dot(forward)
		var w_right : float = wind_direction.dot(right)
		var ang_viento : float = rad_to_deg(atan2(w_right, -w_fwd))

		var eff_mayor : float = abs(sin(deg_to_rad(ang_mayor - ang_viento)))
		var eff_foque : float = abs(sin(deg_to_rad(ang_foque - ang_viento)))
		eff_mayor = max(eff_mayor, eficiencia_minima)
		eff_foque = max(eff_foque, eficiencia_minima)

		factor = eff_mayor * vela_mayor_peso + eff_foque * foque_peso
		if factor < eficiencia_minima:
			factor = eficiencia_minima

	target.apply_central_force(wind_direction * strength_now * factor)

	if debug_print and int(time * 10) % 10 == 0:
		print("[Wind] strength=%.1f N  factor=%.2f" % [strength_now, factor])

func get_wind_speed() -> float:
	return wind_speed_ms

func get_wind_direction() -> float:
	return wind_direction_deg + 90.0
