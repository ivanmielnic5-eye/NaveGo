extends Node

@export var wind_controller_path: NodePath
@export var sailboat_path: NodePath

var wind_controller: Node = null
var sailboat: RigidBody3D = null

func _ready():
	wind_controller = get_node_or_null(wind_controller_path)
	sailboat = get_node_or_null(sailboat_path) as RigidBody3D
	
	if wind_controller == null:
		push_warning("[HeadingWindIntegrator] Wind controller no encontrado.")
	if sailboat == null:
		push_warning("[HeadingWindIntegrator] Sailboat no encontrado.")

func get_navigation_snapshot() -> Dictionary:
	var snapshot = {
		"heading_deg": 0.0,
		"cog_deg": 0.0,
		"sog_knots": 0.0,
		"apparent_wind_speed_ms": 0.0,
		"apparent_wind_angle_deg": 0.0
	}

	if sailboat == null or wind_controller == null:
		return snapshot

	# ---- Datos del barco ----
	var velocity = sailboat.linear_velocity
	var horizontal = Vector2(velocity.x, velocity.z)
	var speed_ms = horizontal.length()
	if speed_ms > 0.05:
		snapshot["sog_knots"] = speed_ms * 1.94384449
		var angle_rad = atan2(velocity.x, -velocity.z)
		snapshot["cog_deg"] = fmod(rad_to_deg(angle_rad) + 360.0, 360.0)

	var basis = sailboat.global_transform.basis
	var forward = -basis.z
	var heading_rad = atan2(forward.x, -forward.z)
	snapshot["heading_deg"] = fmod(rad_to_deg(heading_rad) + 360.0, 360.0)

	# ---- Viento aparente ----
	var wind_speed = 0.0
	var wind_dir_deg = 0.0
	
	# Leer velocidad del viento (CORREGIDO: sin get() con dos argumentos)
	if wind_controller.has_method("get_wind_speed"):
		wind_speed = wind_controller.get_wind_speed()
	else:
		wind_speed = 0.0
	
	# Leer dirección del viento (CORREGIDO: sin get() con dos argumentos)
	if wind_controller.has_method("get_wind_direction"):
		wind_dir_deg = wind_controller.get_wind_direction()
	else:
		wind_dir_deg = 0.0

	# Convertir dirección del viento a vector 3D
	var wind_dir = Vector3(1, 0, 0).rotated(Vector3.UP, deg_to_rad(wind_dir_deg)).normalized()
	
	# Velocidad del barco en vector 3D
	var boat_velocity = sailboat.linear_velocity
	
	# Viento aparente = viento real - velocidad del barco
	var apparent_wind = wind_dir * wind_speed - boat_velocity
	var apparent_speed = apparent_wind.length()
	snapshot["apparent_wind_speed_ms"] = apparent_speed
	
	# Ángulo aparente: ángulo entre el viento aparente y la proa del barco
	if apparent_speed > 0.01:
		var boat_forward = -sailboat.global_transform.basis.z
		var angle = boat_forward.angle_to(apparent_wind)
		snapshot["apparent_wind_angle_deg"] = rad_to_deg(angle)
	else:
		snapshot["apparent_wind_angle_deg"] = 0.0

	return snapshot
