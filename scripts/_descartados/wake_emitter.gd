extends Node3D

# ============================================================
# WAKE EMITTER v3 - Estela con patron de Kelvin + expansion
# ============================================================
# Basado en:
# - Patron de Kelvin: V con semiangulo 19.5 grados (fisica real)
# - Scale curve: la espuma crece durante su vida (se expande)
# - Sub-emitter: al morir una particula grande, nace una chica
#   que se dispersa mas -> simula la bifurcacion de la ola
# - Alta transparencia para que se vea como agua, no humo

@export var sog_min_kn: float = 0.3
@export var sog_max_kn: float = 4.5
@export var foam_color: Color = Color(0.9, 0.94, 1.0, 0.38)
@export var kelvin_half_angle_deg: float = 19.5

var _boat: RigidBody3D = null
var _emisores: Array[GPUParticles3D] = []
var _sub_emisor_popa: GPUParticles3D = null

func _ready() -> void:
	_boat = get_parent() as RigidBody3D
	if _boat == null:
		push_warning("[WakeEmitter] Padre no es RigidBody3D.")
		return

	# --- Sub-emisor (particulas chicas que salen de las grandes) ---
	_sub_emisor_popa = _crear_sub_emisor("FoamSpray", 300)

	# --- Proa babor / estribor (angulo Kelvin) ---
	var ang := deg_to_rad(kelvin_half_angle_deg)
	var dir_babor := Vector3(-sin(ang), 0.0, -cos(ang))
	var dir_estribor := Vector3( sin(ang), 0.0, -cos(ang))
	_emisores.append(_crear_emisor("BowWake_Port", Vector3(-1.2, -0.35, -4.5), 600, dir_babor, false))
	_emisores.append(_crear_emisor("BowWake_Stbd", Vector3( 1.2, -0.35, -4.5), 600, dir_estribor, false))

	# --- Popa: emisor principal con sub-emisor ---
	_emisores.append(_crear_emisor("SternWake", Vector3(0, -0.35, 5.2), 900, Vector3(0, 0.05, 1), true))

	print("[WakeEmitter] Activo v3. Kelvin %.1f grados. %d emisores + 1 sub-emisor." % [kelvin_half_angle_deg, _emisores.size()])

func _crear_emisor(nombre: String, pos_local: Vector3, cantidad: int, dir_local: Vector3, con_subemisor: bool) -> GPUParticles3D:
	var emisor := GPUParticles3D.new()
	emisor.name = nombre
	emisor.position = pos_local
	emisor.amount = cantidad
	emisor.lifetime = 5.5
	emisor.local_coords = false
	emisor.emitting = false
	emisor.one_shot = false
	emisor.visibility_aabb = AABB(Vector3(-100, -5, -100), Vector3(200, 10, 200))
	emisor.randomness = 0.7
	emisor.fixed_fps = 30

	if con_subemisor and _sub_emisor_popa != null:
		emisor.sub_emitter = emisor.get_path_to(_sub_emisor_popa)

	var mat := ParticleProcessMaterial.new()
	mat.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	mat.emission_box_extents = Vector3(0.8, 0.05, 0.5)
	mat.direction = dir_local
	mat.spread = 25.0
	mat.initial_velocity_min = 0.1
	mat.initial_velocity_max = 0.35
	mat.gravity = Vector3(0, -0.1, 0)
	mat.damping_min = 0.3
	mat.damping_max = 0.9
	# Escala: arranca chico, crece, se mantiene, se achica al morir
	mat.scale_min = 0.25
	mat.scale_max = 0.6
	mat.scale_curve = _curve_expansiva()

	var ramp := Gradient.new()
	ramp.set_color(0, Color(foam_color.r, foam_color.g, foam_color.b, 0.0))
	ramp.add_point(0.05, Color(foam_color.r, foam_color.g, foam_color.b, foam_color.a))
	ramp.add_point(0.5, Color(foam_color.r, foam_color.g, foam_color.b, foam_color.a * 0.5))
	ramp.set_color(1, Color(foam_color.r, foam_color.g, foam_color.b, 0.0))
	var ramp_tex := GradientTexture1D.new()
	ramp_tex.gradient = ramp
	mat.color_ramp = ramp_tex
	emisor.process_material = mat
	emisor.draw_pass_1 = _quad_espuma(1.0)
	add_child(emisor)
	return emisor

func _crear_sub_emisor(nombre: String, cantidad: int) -> GPUParticles3D:
	var emisor := GPUParticles3D.new()
	emisor.name = nombre
	emisor.amount = cantidad
	emisor.lifetime = 2.0
	emisor.local_coords = false
	emisor.emitting = true   # El sub-emisor solo emite cuando lo invoca el padre
	emisor.one_shot = false
	emisor.visibility_aabb = AABB(Vector3(-100, -5, -100), Vector3(200, 10, 200))

	var mat := ParticleProcessMaterial.new()
	mat.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
	mat.emission_sphere_radius = 0.5
	mat.direction = Vector3(0, 0.05, 0)
	mat.spread = 180.0    # Se dispersa en todas direcciones -> bifurcacion
	mat.initial_velocity_min = 0.05
	mat.initial_velocity_max = 0.3
	mat.gravity = Vector3(0, -0.05, 0)
	mat.damping_min = 0.5
	mat.damping_max = 1.5
	mat.scale_min = 0.15
	mat.scale_max = 0.35

	var ramp := Gradient.new()
	ramp.set_color(0, Color(foam_color.r, foam_color.g, foam_color.b, 0.0))
	ramp.add_point(0.1, Color(foam_color.r, foam_color.g, foam_color.b, foam_color.a * 0.7))
	ramp.set_color(1, Color(foam_color.r, foam_color.g, foam_color.b, 0.0))
	var ramp_tex := GradientTexture1D.new()
	ramp_tex.gradient = ramp
	mat.color_ramp = ramp_tex
	emisor.process_material = mat
	emisor.draw_pass_1 = _quad_espuma(0.6)
	add_child(emisor)
	return emisor

func _quad_espuma(tamano: float) -> QuadMesh:
	var quad := QuadMesh.new()
	quad.size = Vector2(tamano, tamano)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_FIXED_Y
	mat.vertex_color_use_as_albedo = true
	mat.albedo_color = Color(1, 1, 1, 1)
	# Textura radial con borde irregular (mas "espuma" que "pelota")
	var grad := Gradient.new()
	grad.set_color(0, Color(1, 1, 1, 0.85))
	grad.add_point(0.5, Color(1, 1, 1, 0.4))
	grad.set_color(1, Color(1, 1, 1, 0.0))
	var tex := GradientTexture2D.new()
	tex.gradient = grad
	tex.width = 64
	tex.height = 64
	tex.fill = GradientTexture2D.FILL_RADIAL
	tex.fill_from = Vector2(0.5, 0.5)
	tex.fill_to = Vector2(1.0, 0.5)
	mat.albedo_texture = tex
	quad.material = mat
	return quad

func _curve_expansiva() -> CurveTexture:
	# Crece durante toda la vida -> efecto de "abrirse"
	var c := Curve.new()
	c.add_point(Vector2(0.0, 0.3))
	c.add_point(Vector2(0.3, 0.8))
	c.add_point(Vector2(0.7, 1.5))
	c.add_point(Vector2(1.0, 2.2))
	var ct := CurveTexture.new()
	ct.curve = c
	return ct

func _physics_process(_delta: float) -> void:
	if _boat == null or _emisores.is_empty():
		return
	var sog_kn: float = _boat.linear_velocity.length() * 1.94384
	var t: float = clamp((sog_kn - sog_min_kn) / (sog_max_kn - sog_min_kn), 0.0, 1.0)
	var emitir := t > 0.05
	for em in _emisores:
		em.emitting = emitir
		em.amount_ratio = t
