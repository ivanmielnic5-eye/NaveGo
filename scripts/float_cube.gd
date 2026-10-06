extends RigidBody3D

# ============================================================
# FLOTABILIDAD POR MALLA FISICA (Arquimedes real)
# ============================================================
# Cada punto de la malla tiene posicion local (x, y, z) y area (m2).
# Fuerza en cada punto: F = rho * g * area * profundidad
#   rho  = 1025 kg/m3  (agua salada)
#   g    = 9.8 m/s2
#   area = area del elemento de casco (m2)
#   prof = cuanto esta el punto bajo el agua (m)

@export var water_density: float = 1025.0   # kg/m3 (agua salada)
@export var forward_drag_coef: float = 0.05   # friccion frontal cuadratica
@export var lateral_drag_coef: float = 1.20   # friccion lateral (frena deriva)
@export var angular_drag_coef: float = 0.35   # friccion angular
@export var vertical_drag_coef: float = 45.0    # resistencia al movimiento vertical (subir/bajar)

# ============================================================
# MALLA DEL CASCO (168 puntos extraidos del .glb)
# Formato Vector4: (x, y, z, area)
# ============================================================
const HULL_POINTS: Array[Vector4] = [
	Vector4(-0.0030, -1.4080, -0.2590, 0.06795),
	Vector4(0.0080, -1.4080, -0.2590, 0.06872),
	Vector4(0.0110, -1.4050, -0.7400, 0.07762),
	Vector4(-0.0060, -1.4050, -0.7390, 0.07710),
	Vector4(-0.0050, -1.4030, -1.1920, 0.04313),
	Vector4(0.0090, -1.4030, -1.1920, 0.04283),
	Vector4(0.0100, -1.3990, -1.5230, 0.02134),
	Vector4(-0.0050, -1.3990, -1.5220, 0.02213),
	Vector4(-0.0070, -1.3870, 0.0290, 0.03647),
	Vector4(0.0110, -1.3870, 0.0290, 0.03613),
	Vector4(-0.0050, -1.3680, -1.5410, 0.02179),
	Vector4(0.0090, -1.3680, -1.5410, 0.02256),
	Vector4(-0.1000, -1.1140, -0.5210, 0.17413),
	Vector4(0.1100, -1.1140, -0.5210, 0.17419),
	Vector4(-0.0750, -1.1140, 0.0190, 0.15443),
	Vector4(0.0820, -1.1140, 0.0190, 0.15430),
	Vector4(-0.0040, -1.1140, 0.4350, 0.08300),
	Vector4(0.0080, -1.1140, 0.4350, 0.08251),
	Vector4(-0.0770, -1.1060, -1.0260, 0.16082),
	Vector4(0.0850, -1.1060, -1.0260, 0.16115),
	Vector4(-0.0040, -1.1030, -1.4120, 0.04394),
	Vector4(0.0080, -1.1030, -1.4120, 0.04470),
	Vector4(-0.0210, -1.0430, -4.8510, 0.00763),
	Vector4(0.0250, -1.0430, -4.8510, 0.00515),
	Vector4(-0.0210, -1.0270, -4.8680, 0.07627),
	Vector4(0.0250, -1.0270, -4.8680, 0.08253),
	Vector4(-0.0130, -1.0260, -4.3770, 0.00515),
	Vector4(0.0160, -1.0260, -4.3770, 0.00891),
	Vector4(-0.0120, -1.0090, -4.3550, 0.17306),
	Vector4(0.0160, -1.0090, -4.3550, 0.16925),
	Vector4(-0.0100, -0.7880, -1.2700, 0.00463),
	Vector4(0.0140, -0.7880, -1.2700, 0.00369),
	Vector4(-0.1510, -0.7810, 0.3780, 0.19187),
	Vector4(0.1510, -0.7810, 0.3780, 0.19065),
	Vector4(-0.1800, -0.7800, -0.2660, 0.19657),
	Vector4(0.1830, -0.7800, -0.2660, 0.19464),
	Vector4(-0.0070, -0.7800, 0.9340, 0.06833),
	Vector4(0.0100, -0.7800, 0.9340, 0.10573),
	Vector4(-0.1570, -0.7640, -0.8740, 0.16928),
	Vector4(0.1610, -0.7640, -0.8740, 0.13363),
	Vector4(0.0270, -0.7580, -1.2280, 0.04793),
	Vector4(-0.0230, -0.7580, -1.2270, 0.04786),
	Vector4(-0.0100, -0.7360, -1.2810, 0.05400),
	Vector4(0.0140, -0.7360, -1.2810, 0.05540),
	Vector4(-0.2060, -0.5160, -0.0440, 0.10856),
	Vector4(0.2200, -0.5160, -0.0440, 0.11135),
	Vector4(-0.0050, -0.5140, 1.5320, 0.07318),
	Vector4(0.0090, -0.5140, 1.5320, 0.04460),
	Vector4(-0.1700, -0.5130, 0.7750, 0.11200),
	Vector4(0.1850, -0.5130, 0.7750, 0.11285),
	Vector4(-0.0120, -0.5060, 1.5650, 0.01625),
	Vector4(0.0170, -0.5060, 1.5650, 0.01953),
	Vector4(-0.1820, -0.5040, -0.8390, 0.09530),
	Vector4(0.1930, -0.5040, -0.8390, 0.12297),
	Vector4(0.0020, -0.5040, 1.5940, 0.04344),
	Vector4(-0.2240, -0.5010, -0.0340, 0.19388),
	Vector4(0.2390, -0.5010, -0.0340, 0.18947),
	Vector4(-0.1870, -0.5000, 0.7890, 0.20473),
	Vector4(0.2030, -0.5000, 0.7890, 0.20513),
	Vector4(-0.1060, -0.4960, 1.5940, 0.23026),
	Vector4(0.1110, -0.4960, 1.5940, 0.21731),
	Vector4(-0.2010, -0.4850, -0.8370, 0.21590),
	Vector4(0.2120, -0.4850, -0.8370, 0.27347),
	Vector4(-0.0060, -0.4840, -1.5640, 0.03750),
	Vector4(0.0100, -0.4840, -1.5640, 0.03938),
	Vector4(-0.0060, -0.4650, -1.6410, 0.17758),
	Vector4(0.0080, -0.4650, -1.6410, 0.24730),
	Vector4(0.0020, -0.4600, 2.4050, 0.07313),
	Vector4(-0.0910, -0.4500, 2.4050, 0.21849),
	Vector4(0.0950, -0.4500, 2.4050, 0.22280),
	Vector4(-0.6740, -0.4490, -0.0340, 0.39880),
	Vector4(0.6780, -0.4490, -0.0340, 0.38639),
	Vector4(-0.6600, -0.4480, -0.8370, 0.41088),
	Vector4(0.6640, -0.4480, -0.8370, 0.34052),
	Vector4(-0.6180, -0.4290, -1.6420, 0.52967),
	Vector4(0.6220, -0.4290, -1.6420, 0.45567),
	Vector4(-0.6240, -0.4080, 0.7890, 0.38613),
	Vector4(0.6280, -0.4080, 0.7890, 0.36852),
	Vector4(-0.0160, -0.3720, -2.4440, 0.30865),
	Vector4(0.0140, -0.3720, -2.4440, 0.17376),
	Vector4(0.0020, -0.3670, 3.2330, 0.04388),
	Vector4(-0.0460, -0.3510, 3.2330, 0.19269),
	Vector4(0.0500, -0.3510, 3.2330, 0.19599),
	Vector4(-0.5590, -0.3420, 1.5940, 0.37519),
	Vector4(0.5630, -0.3420, 1.5940, 0.37012),
	Vector4(-0.5760, -0.3400, -2.4440, 0.36718),
	Vector4(0.5790, -0.3400, -2.4440, 0.51852),
	Vector4(-0.0120, -0.2840, -4.0930, 0.12145),
	Vector4(0.0160, -0.2840, -4.0930, 0.12544),
	Vector4(-0.0080, -0.2740, -3.2480, 0.03093),
	Vector4(0.0130, -0.2740, -3.2480, 0.01607),
	Vector4(-0.0220, -0.2530, -3.2480, 0.02018),
	Vector4(0.0270, -0.2530, -3.2480, 0.03061),
	Vector4(-0.0120, -0.2470, -4.0350, 0.02288),
	Vector4(0.0160, -0.2470, -4.0350, 0.02329),
	Vector4(-0.0560, -0.2460, -3.2480, 0.17363),
	Vector4(0.0600, -0.2460, -3.2480, 0.20812),
	Vector4(-0.0210, -0.2410, -4.8780, 0.23666),
	Vector4(0.0250, -0.2410, -4.8780, 0.22654),
	Vector4(-0.4730, -0.2360, 2.4050, 0.36641),
	Vector4(0.4770, -0.2360, 2.4050, 0.35887),
	Vector4(-1.1540, -0.2210, -1.6420, 0.41076),
	Vector4(1.1570, -0.2210, -1.6420, 0.40657),
	Vector4(-0.4860, -0.2190, -3.2480, 0.39860),
	Vector4(0.4900, -0.2190, -3.2480, 0.37693),
	Vector4(-1.1680, -0.2170, -0.8370, 0.39552),
	Vector4(1.1720, -0.2170, -0.8370, 0.40165),
	Vector4(0.0020, -0.2110, 3.9530, 0.01595),
	Vector4(-1.1230, -0.1950, -0.0340, 0.38321),
	Vector4(1.1270, -0.1950, -0.0340, 0.39436),
	Vector4(-0.0220, -0.1850, 3.9570, 0.11994),
	Vector4(0.0250, -0.1850, 3.9570, 0.06498),
	Vector4(-1.0950, -0.1830, -2.4440, 0.40630),
	Vector4(1.0990, -0.1830, -2.4440, 0.39827),
	Vector4(-0.0480, -0.1420, -4.0710, 0.08515),
	Vector4(0.0520, -0.1420, -4.0710, 0.08282),
	Vector4(-0.0020, -0.1390, 4.0590, 0.00931),
	Vector4(-0.0700, -0.1240, -4.0710, 0.13525),
	Vector4(0.0740, -0.1240, -4.0710, 0.16274),
	Vector4(-0.0170, -0.1240, 4.0520, 0.03156),
	Vector4(0.0140, -0.1240, 4.0520, 0.03214),
	Vector4(-0.9860, -0.1060, 0.7890, 0.36933),
	Vector4(0.9900, -0.1060, 0.7890, 0.37311),
	Vector4(-0.3990, -0.0870, -4.0710, 0.32855),
	Vector4(0.4030, -0.0870, -4.0710, 0.32238),
	Vector4(-0.9700, -0.0770, -3.2480, 0.38841),
	Vector4(0.9740, -0.0770, -3.2480, 0.38725),
	Vector4(-0.3090, -0.0140, 3.2330, 0.33296),
	Vector4(0.3130, -0.0140, 3.2330, 0.23534),
	Vector4(-0.8380, 0.0040, 1.5940, 0.29669),
	Vector4(0.8420, 0.0040, 1.5940, 0.24191),
	Vector4(-0.0450, 0.0180, -4.8780, 0.04301),
	Vector4(0.0490, 0.0180, -4.8780, 0.05009),
	Vector4(-0.0630, 0.0380, -4.8780, 0.04185),
	Vector4(0.0670, 0.0380, -4.8780, 0.08242),
	Vector4(-0.8450, 0.0510, -4.0710, 0.30163),
	Vector4(0.8490, 0.0510, -4.0710, 0.29035),
	Vector4(-0.2900, 0.0720, -4.8740, 0.14122),
	Vector4(0.0020, 0.0720, -4.8740, 0.01210),
	Vector4(0.2940, 0.0720, -4.8740, 0.15767),
	Vector4(-0.6530, 0.1470, -4.8520, 0.17193),
	Vector4(0.0020, 0.1470, -4.8520, 0.02462),
	Vector4(0.6560, 0.1470, -4.8520, 0.10792),
	Vector4(-1.4130, 0.1480, -1.6420, 0.17903),
	Vector4(1.4170, 0.1480, -1.6420, 0.18170),
	Vector4(-1.3900, 0.1550, -0.8370, 0.17484),
	Vector4(1.3940, 0.1550, -0.8370, 0.17711),
	Vector4(-1.3900, 0.1600, -2.4440, 0.18250),
	Vector4(1.3940, 0.1600, -2.4440, 0.18207),
	Vector4(-0.6300, 0.1650, 2.4050, 0.22809),
	Vector4(0.6340, 0.1650, 2.4050, 0.18410),
	Vector4(-1.3000, 0.2010, -0.0340, 0.17899),
	Vector4(1.3040, 0.2010, -0.0340, 0.17793),
	Vector4(-0.1080, 0.2210, 4.0590, 0.13593),
	Vector4(0.1120, 0.2210, 4.0590, 0.13979),
	Vector4(-1.2880, 0.2270, -3.2480, 0.18369),
	Vector4(1.2920, 0.2270, -3.2480, 0.12134),
	Vector4(-1.1240, 0.2950, 0.7890, 0.11799),
	Vector4(1.1280, 0.2950, 0.7890, 0.17906),
	Vector4(-0.4180, 0.3160, 3.2330, 0.10038),
	Vector4(0.4220, 0.3160, 3.2330, 0.11181),
	Vector4(-1.0990, 0.3330, -4.0710, 0.16652),
	Vector4(1.1020, 0.3330, -4.0710, 0.05110),
	Vector4(-0.0120, 0.3420, 4.4330, 0.02689),
	Vector4(0.0020, 0.3420, 4.4330, 0.02731),
	Vector4(-0.0050, 0.3420, 4.4480, 0.00282),
	Vector4(-0.9410, 0.3830, 1.5940, 0.05534),
	Vector4(0.9450, 0.3830, 1.5940, 0.11248),
]

@onready var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")

var water_advanced: Node = null
var wind_controller: Node = null
var wind_force_multiplier: float = 1.0

func _ready() -> void:
	axis_lock_angular_x = false
	axis_lock_angular_z = false
	linear_damp = 0.05
	angular_damp = 0.8
	center_of_mass_mode = RigidBody3D.CENTER_OF_MASS_MODE_CUSTOM
	center_of_mass = Vector3(0, -1.2, 0)

	water_advanced = get_tree().root.find_child("Water", true, false)
	wind_controller = get_tree().root.find_child("Wind", true, false)
	if wind_controller:
		print("[FloatMalla] Wind controller encontrado.")
	else:
		push_warning("[FloatMalla] Wind controller NO encontrado.")
	print("[FloatMalla] Activo. %d puntos de malla. Rho=%.0f kg/m3." % [HULL_POINTS.size(), water_density])

func _physics_process(_delta: float) -> void:
	if water_advanced == null or not water_advanced.has_method("get_water_height"):
		return

	var xform := global_transform
	var submerged_any := false
	var center_of_buoyancy := Vector3.ZERO
	var total_area_sumergida := 0.0
	var torque_extra := Vector3.ZERO

	# ============================================================
	# 1. FLOTABILIDAD (Arquimedes real por punto)
	# ============================================================
	for p in HULL_POINTS:
		var local_pos := Vector3(p.x, p.y, p.z)
		var area := p.w
		var world_pos: Vector3 = xform * local_pos
		var water_height: float = water_advanced.get_water_height(world_pos)
		var depth: float = water_height - world_pos.y

		if depth > 0.0:
			submerged_any = true
			total_area_sumergida += area
			# Fuerza hacia arriba: F = rho * g * A * d
			var fuerza_arriba: float = water_density * gravity * area * depth
			apply_force(Vector3.UP * fuerza_arriba, world_pos - global_position)
			center_of_buoyancy += world_pos * area

	# ============================================================
	# 2. TORQUE POR DISTRIBUCION DE EMPUJES (roll/pitch natural)
	# ============================================================
	# El RigidBody ya genera torque desde el apply_force con offset.
	# No hace falta un resorte artificial. Confiamos en la fisica.

	# ============================================================
	# 3. DRAG HIDRODINAMICO CUADRATICO
	# ============================================================
	if submerged_any:
		var forward_dir: Vector3 = -global_transform.basis.z
		var v := linear_velocity
		var v_forward: float = v.dot(forward_dir)
		var v_lateral: Vector3 = v - forward_dir * v_forward

		# Friccion cuadratica: F = -k * v * |v|
		var drag_forward: Vector3 = -forward_dir * v_forward * abs(v_forward) * forward_drag_coef * total_area_sumergida / 10.0
		var drag_lateral: Vector3 = -v_lateral * v_lateral.length() * lateral_drag_coef * total_area_sumergida / 10.0
		apply_central_force(drag_forward + drag_lateral)

		# Friccion angular cuadratica
		var w: Vector3 = angular_velocity
		apply_torque(-w * w.length() * angular_drag_coef)

		# Friccion vertical cuadratica: el agua frena el subir/bajar
		# F = -k * v_y * |v_y| (solo componente Y)
		var v_y: float = linear_velocity.y
		apply_central_force(Vector3(0, -v_y * abs(v_y) * vertical_drag_coef * total_area_sumergida / 10.0, 0))

	# ============================================================
	# 4. VIENTO
	# ============================================================
	if wind_controller != null and wind_controller.has_method("get_wind_force"):
		var wind_force: Vector3 = wind_controller.get_wind_force()
		if wind_force.length() > 0.01:
			apply_central_force(wind_force * wind_force_multiplier)
