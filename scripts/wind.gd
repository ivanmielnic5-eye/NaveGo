extends Node3D

# ═══════════════════════════════════════════════════
# VARIABLES EXPORTADAS (aparecen en el Inspector)
# ═══════════════════════════════════════════════════

@export var target_path: NodePath

@export_group("Intensidad del Viento")
@export var wind_speed_ms: float = 5.0  # velocidad real del viento en m/s (para lectura)
@export_range(0.0, 50.0, 0.5) var wind_strength: float = 1.5
@export_range(0.0, 10.0, 0.1) var gust_amplitude: float = 3.0
@export_range(0.0, 5.0, 0.1) var gust_frequency: float = 0.7

@export_group("Dirección del Viento")
@export_range(0.0, 360.0, 1.0) var wind_direction_deg: float = 0.0
@export_range(0.0, 5.0, 0.1) var direction_variation: float = 0.3

@export_group("Debug")
@export var debug_print: bool = false

# ═══════════════════════════════════════════════════
# VARIABLES INTERNAS
# ═══════════════════════════════════════════════════

var target: RigidBody3D
var time: float = 0.0

# ═══════════════════════════════════════════════════
# LÓGICA
# ═══════════════════════════════════════════════════

func _ready() -> void:
	target = get_node_or_null(target_path) as RigidBody3D
	if target == null:
		push_warning("[Wind] Target no encontrado.")
	else:
		print("[Wind] Target: ", target.name)

func _physics_process(delta: float) -> void:
	if target == null:
		return

	time += delta

	# Ráfagas: oscila el viento alrededor de wind_strength
	var gust = sin(time * gust_frequency) * gust_amplitude
	var strength_now = wind_strength * 1000.0 + gust * 100.0

	# Dirección: varía lentamente alrededor de wind_direction_deg
	var dir_offset = sin(time * direction_variation) * 15.0
	var angle_rad = deg_to_rad(wind_direction_deg + dir_offset)
	var wind_direction = Vector3(sin(angle_rad), 0.0, cos(angle_rad)).normalized()

	# Aplicar fuerza (sin * delta, Godot ya lo integra)
	target.apply_central_force(wind_direction * strength_now)

	if debug_print and int(time * 10) % 10 == 0:
		print("[Wind] strength: %.1f N, dir: %.0f°" % [strength_now, wind_direction_deg + dir_offset])

func get_wind_speed() -> float:
	return wind_speed_ms


func get_wind_direction() -> float:
	# Integrator usa base Vector3(1,0,0); wind.gd usa Vector3(0,0,1).
	# Sumamos 90 para alinear convenciones.
	return wind_direction_deg + 90.0
