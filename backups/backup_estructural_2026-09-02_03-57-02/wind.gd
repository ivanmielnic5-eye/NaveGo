extends Node3D

@export var target_path: NodePath

var target: RigidBody3D
var time: float = 0.0

func _ready() -> void:
	target = get_node_or_null(target_path) as RigidBody3D

func _physics_process(delta: float) -> void:
	if target == null:
		return

	time += delta

	# Viento lateral con ráfagas
	var gust = sin(time * 0.7) * 3.0
	var wind_strength = 8.0 + gust
	var wind_direction = Vector3(1.0, 0.0, 0.2).rotated(Vector3.UP, sin(time * 0.3) * 1.5).normalized()

	# Fuerza proporcional a la masa para notarse
	target.apply_central_force(wind_direction * wind_strength * target.mass * delta)
