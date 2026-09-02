extends Node3D

@export var sailboat_path: NodePath

var sailboat: RigidBody3D = null

func _ready():
	sailboat = get_node_or_null(sailboat_path) as RigidBody3D
	if sailboat == null:
		push_warning("[Main] SailboatBody no encontrado.")
	else:
		print("[Main] SailboatBody encontrado.")

func _physics_process(delta):
	if sailboat == null:
		return

	# ---- CONTROL MANUAL (WASD) ----
	var force = 50000.0
	var torque = 10000.0
	var apply_force = Vector3.ZERO
	var apply_torque = Vector3.ZERO
	var forward = sailboat.global_transform.basis.z

	if Input.is_key_pressed(KEY_W):
		apply_force += forward * force
	if Input.is_key_pressed(KEY_S):
		apply_force += -forward * force
	if Input.is_key_pressed(KEY_A):
		apply_torque += Vector3.UP * torque
	if Input.is_key_pressed(KEY_D):
		apply_torque += -Vector3.UP * torque

	if apply_force != Vector3.ZERO:
		sailboat.apply_central_force(apply_force)
	if apply_torque != Vector3.ZERO:
		sailboat.apply_torque(apply_torque)
