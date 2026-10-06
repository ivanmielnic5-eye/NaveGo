extends Node3D

# ============================================================
# AGUA REALISTA - Suma de 4 olas de Gerstner simplificadas
# ============================================================
# Altura fisica calculada aqui (para el RigidBody).
# Altura visual calculada en water.gdshader (mismo calculo, misma formula).
# El tiempo _time se pasa al shader como uniform para que las dos
# coincidan exactamente (lo que se ve = lo que el barco siente).

@export var water_level: float = 0.0

@export var wave1_amplitude: float = 0.5
@export var wave1_wavelength: float = 30.0
@export var wave1_dir_deg: float = 90.0
@export var wave1_speed: float = 3.0

@export var wave2_amplitude: float = 0.25
@export var wave2_wavelength: float = 18.0
@export var wave2_dir_deg: float = 135.0
@export var wave2_speed: float = 2.2

@export var wave3_amplitude: float = 0.15
@export var wave3_wavelength: float = 12.0
@export var wave3_dir_deg: float = 45.0
@export var wave3_speed: float = 1.8

@export var wave4_amplitude: float = 0.08
@export var wave4_wavelength: float = 6.0
@export var wave4_dir_deg: float = 200.0
@export var wave4_speed: float = 1.2

var _time: float = 0.0
var _boat: Node3D = null
var _water_mesh: MeshInstance3D = null
var _shader_mat: ShaderMaterial = null

func _ready() -> void:
	_boat = get_tree().root.find_child("SailboatBody", true, false)
	_water_mesh = get_node_or_null("WaterMesh")
	if _water_mesh != null:
		var mat = _water_mesh.material_override
		if mat != null and mat is ShaderMaterial:
			_shader_mat = mat
			# Sincronizar parametros del shader con los del script
			_sync_shader_uniforms()

func _sync_shader_uniforms() -> void:
	if _shader_mat == null: return
	_shader_mat.set_shader_parameter("water_level", water_level)
	_shader_mat.set_shader_parameter("wave1_amplitude", wave1_amplitude)
	_shader_mat.set_shader_parameter("wave1_wavelength", wave1_wavelength)
	_shader_mat.set_shader_parameter("wave1_dir_deg", wave1_dir_deg)
	_shader_mat.set_shader_parameter("wave1_speed", wave1_speed)
	_shader_mat.set_shader_parameter("wave2_amplitude", wave2_amplitude)
	_shader_mat.set_shader_parameter("wave2_wavelength", wave2_wavelength)
	_shader_mat.set_shader_parameter("wave2_dir_deg", wave2_dir_deg)
	_shader_mat.set_shader_parameter("wave2_speed", wave2_speed)
	_shader_mat.set_shader_parameter("wave3_amplitude", wave3_amplitude)
	_shader_mat.set_shader_parameter("wave3_wavelength", wave3_wavelength)
	_shader_mat.set_shader_parameter("wave3_dir_deg", wave3_dir_deg)
	_shader_mat.set_shader_parameter("wave3_speed", wave3_speed)
	_shader_mat.set_shader_parameter("wave4_amplitude", wave4_amplitude)
	_shader_mat.set_shader_parameter("wave4_wavelength", wave4_wavelength)
	_shader_mat.set_shader_parameter("wave4_dir_deg", wave4_dir_deg)
	_shader_mat.set_shader_parameter("wave4_speed", wave4_speed)

func _process(delta: float) -> void:
	_time += delta
	if _shader_mat != null:
		_shader_mat.set_shader_parameter("wave_time", _time)
	if _water_mesh != null and _boat != null:
		# Seguir al barco en XZ para que el plano visible siempre lo cubra
		_water_mesh.global_position.x = _boat.global_position.x
		_water_mesh.global_position.z = _boat.global_position.z

func _wave_phase(world_pos: Vector3, dir_deg: float, wavelength: float, speed: float) -> float:
	var dir_rad := deg_to_rad(dir_deg)
	var k_x := cos(dir_rad)
	var k_z := sin(dir_rad)
	var k := TAU / wavelength
	return k * (world_pos.x * k_x + world_pos.z * k_z) - k * speed * _time

func get_water_height(world_pos: Vector3) -> float:
	var h := water_level
	h += wave1_amplitude * sin(_wave_phase(world_pos, wave1_dir_deg, wave1_wavelength, wave1_speed))
	h += wave2_amplitude * sin(_wave_phase(world_pos, wave2_dir_deg, wave2_wavelength, wave2_speed))
	h += wave3_amplitude * sin(_wave_phase(world_pos, wave3_dir_deg, wave3_wavelength, wave3_speed))
	h += wave4_amplitude * sin(_wave_phase(world_pos, wave4_dir_deg, wave4_wavelength, wave4_speed))
	return h

func get_water_normal(world_pos: Vector3) -> Vector3:
	var eps := 0.3
	var h := get_water_height(world_pos)
	var h_x := get_water_height(world_pos + Vector3(eps, 0, 0))
	var h_z := get_water_height(world_pos + Vector3(0, 0, eps))
	var dx := (h_x - h) / eps
	var dz := (h_z - h) / eps
	return Vector3(-dx, 1.0, -dz).normalized()
