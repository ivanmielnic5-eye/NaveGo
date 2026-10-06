extends Node3D

@export var sailboat_path: NodePath
@export var wasd_force: float = 6000.0
@export var wasd_torque: float = 3500.0

var sailboat: RigidBody3D = null

func _ready():
	sailboat = get_node_or_null(sailboat_path) as RigidBody3D
	if sailboat == null:
		push_warning("[Main] SailboatBody no encontrado.")
	else:
		print("[Main] SailboatBody encontrado.")
		# _crear_marcador_meta()   # desactivado: el muelle visual reemplaza la boya

func _crear_marcador_meta():
	# Marca visual de Puerto Esperanza en (200, 0)
	var meta_pos = Vector3(200.0, 0.0, 0.0)

	# Esfera brillante
	var sphere = MeshInstance3D.new()
	var sphere_mesh = SphereMesh.new()
	sphere_mesh.radius = 20.0
	sphere_mesh.height = 40.0
	sphere.mesh = sphere_mesh
	var mat = StandardMaterial3D.new()
	mat.albedo_color = Color(1.0, 0.2, 0.2, 1.0)
	mat.emission_enabled = true
	mat.emission = Color(1.0, 0.3, 0.1)
	mat.emission_energy_multiplier = 3.0
	sphere.material_override = mat
	sphere.position = meta_pos + Vector3(0, 30, 0)
	add_child(sphere)

	# Poste vertical
	var post = MeshInstance3D.new()
	var cyl = CylinderMesh.new()
	cyl.top_radius = 3.0
	cyl.bottom_radius = 3.0
	cyl.height = 200.0
	post.mesh = cyl
	var mat_post = StandardMaterial3D.new()
	mat_post.albedo_color = Color(1.0, 0.8, 0.0, 1.0)
	mat_post.emission_enabled = true
	mat_post.emission = Color(1.0, 0.8, 0.0)
	mat_post.emission_energy_multiplier = 2.0
	post.material_override = mat_post
	post.position = meta_pos + Vector3(0, 100, 0)
	add_child(post)

	# Etiqueta
	var label = Label3D.new()
	label.text = "Puerto Esperanza"
	label.font_size = 128
	label.position = meta_pos + Vector3(0, 220, 0)
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	add_child(label)

	print("[Main] Marcador de Puerto Esperanza creado en (200, 0)")


func _physics_process(delta):
	if sailboat == null:
		return

	# ---- CONTROL MANUAL (WASD) ----
	var force = wasd_force
	var torque = wasd_torque
	var apply_force = Vector3.ZERO
	var apply_torque = Vector3.ZERO
	var forward = -sailboat.global_transform.basis.z

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
