extends RigidBody3D

# ============================================================
# PARÁMETROS DE FLOTABILIDAD
# ============================================================
@export var float_force: float = 120.0       # Fuerza de flotabilidad (ajusta según calado deseado)
@export var water_drag: float = 0.03
@export var water_angular_drag: float = 0.03

# ============================================================
# PARÁMETROS DE BALANCEO (ROLL Y PITCH)
# ============================================================
@export var roll_stiffness: float = 4.0      # Rigidez del balanceo lateral (menos = más balanceo)
@export var pitch_stiffness: float = 4.0     # Rigidez del cabeceo (menos = más cabeceo)
@export var roll_damping: float = 0.8        # Amortiguación del balanceo
@export var pitch_damping: float = 0.8       # Amortiguación del cabeceo

# ============================================================
# REFERENCIAS Y ESTADO
# ============================================================
@onready var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")

var water_advanced: Node = null
var wind_controller: Node = null
var wind_force_multiplier: float = 1.0       # Ajusta según necesites (empieza bajo)
var probes: Array[Node] = []

func _ready() -> void:
	# Liberar rotaciones para permitir balanceo
	axis_lock_angular_x = false
	axis_lock_angular_z = false
	linear_damp = 0.1
	angular_damp = 0.5
	center_of_mass_mode = RigidBody3D.CENTER_OF_MASS_MODE_CUSTOM
	center_of_mass = Vector3(0, -1.5, 0)  # Centro de masa bajo para estabilidad

	# Buscar el nodo de agua avanzada
	water_advanced = get_tree().root.find_child("Water", true, false)

	# Buscar el controlador de viento
	wind_controller = get_tree().root.find_child("Wind", true, false)
	if wind_controller:
		print("[FloatCube] Wind controller encontrado.")
	else:
		push_warning("[FloatCube] Wind controller NO encontrado.")

	# Buscar los probes de flotabilidad
	var probe_container = get_node_or_null("ProbeContainer")
	if probe_container:
		probes = probe_container.get_children()
		print("[FloatCube] Encontrados %d probes." % probes.size())

func _physics_process(delta: float) -> void:
	if water_advanced == null or not water_advanced.has_method("get_water_height"):
		return

	var submerged := false
	var center_of_buoyancy := Vector3.ZERO
	var num_active_probes := 0
	var total_vertical_force := Vector3.ZERO

	# ============================================================
	# 1. CALCULAR FLOTABILIDAD (fuerza vertical en cada probe)
	# ============================================================
	for p in probes:
		var world_pos = p.global_position
		var water_height = water_advanced.get_water_height(world_pos)
		var depth = water_height - world_pos.y

		if depth > 0:
			submerged = true
			num_active_probes += 1
			var force = Vector3.UP * float_force * gravity * depth
			apply_force(force, world_pos - global_position)
			total_vertical_force += force
			center_of_buoyancy += world_pos

	# ============================================================
	# 2. CALCULAR PENDIENTE DE LA OLA Y APLICAR TORQUE (balanceo)
	# ============================================================
	if num_active_probes > 0:
		center_of_buoyancy /= num_active_probes

		# Calcular pendiente de la ola en el centro de flotabilidad
		var eps = 0.5
		var h_center = water_advanced.get_water_height(center_of_buoyancy)
		var h_x = water_advanced.get_water_height(center_of_buoyancy + Vector3(eps, 0, 0))
		var h_z = water_advanced.get_water_height(center_of_buoyancy + Vector3(0, 0, eps))
		var slope_x = (h_x - h_center) / eps  # Pendiente en X (causa roll)
		var slope_z = (h_z - h_center) / eps  # Pendiente en Z (causa pitch)

		# Ángulos objetivo (el barco tiende a alinearse con la pendiente)
		var target_roll = slope_x * 0.4   # Factor de sensibilidad
		var target_pitch = slope_z * 0.4

		# Torque restaurador (como un resorte angular)
		var current_rotation = rotation
		var torque_x = -roll_stiffness * (current_rotation.x - target_roll) - roll_damping * angular_velocity.x
		var torque_z = -pitch_stiffness * (current_rotation.z - target_pitch) - pitch_damping * angular_velocity.z
		apply_torque(Vector3(torque_x, 0, torque_z))

	# ============================================================
	# 3. AMORTIGUACIÓN HIDRODINÁMICA
	# ============================================================
	if submerged:
		linear_velocity *= 1 - water_drag
		angular_velocity *= 1 - water_angular_drag

	# ============================================================
	# 4. APLICAR FUERZA DEL VIENTO REAL
	# ============================================================
	if wind_controller != null and wind_controller.has_method("get_wind_force"):
		var wind_force = wind_controller.get_wind_force()
		if wind_force.length() > 0.01:  # Evitar aplicar fuerzas insignificantes
			apply_central_force(wind_force * wind_force_multiplier)
