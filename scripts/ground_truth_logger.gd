extends Node

@export var target_path: NodePath
@export var log_interval_s: float = 0.0166
@export var autostart: bool = true

var target: RigidBody3D = null
var file: FileAccess = null
var time_accum: float = 0.0
var start_unix_ms: int = 0
var filepath: String = ""

func _ready() -> void:
	target = get_node_or_null(target_path) as RigidBody3D
	if target == null:
		push_warning("[GroundTruth] Target no encontrado.")
		return
	if autostart:
		start_logging()

func start_logging() -> void:
	start_unix_ms = int(Time.get_unix_time_from_system() * 1000)
	filepath = "user://ground_truth_%d.jsonl" % start_unix_ms
	file = FileAccess.open(filepath, FileAccess.WRITE)
	if file == null:
		push_warning("[GroundTruth] No se pudo abrir archivo.")
		return
	print("[GroundTruth] Logging en: ", filepath)

func stop_logging() -> void:
	if file != null:
		file.close()
		file = null
		print("[GroundTruth] Detenido.")

func _process(delta: float) -> void:
	if file == null or target == null:
		return
	time_accum += delta
	if time_accum < log_interval_s:
		return
	time_accum = 0.0
	var now_ms = int(Time.get_unix_time_from_system() * 1000)
	var elapsed_s = (now_ms - start_unix_ms) / 1000.0
	var pos = target.global_position
	var vel = target.linear_velocity
	var rot = target.global_rotation
	var horizontal = Vector2(vel.x, vel.z)
	var sog_kn = horizontal.length() * 1.94384
	var cog_deg = 0.0
	if horizontal.length() > 0.05:
		cog_deg = fmod(rad_to_deg(atan2(vel.x, -vel.z)) + 360.0, 360.0)
	var forward = -target.global_transform.basis.z
	var hdg_deg = fmod(rad_to_deg(atan2(forward.x, -forward.z)) + 360.0, 360.0)
	var line = {
		"timestamp": now_ms,
		"elapsed_s": elapsed_s,
		"pos_x": pos.x,
		"pos_y": pos.y,
		"pos_z": pos.z,
		"sog_kn": sog_kn,
		"cog_deg": cog_deg,
		"hdg_deg": hdg_deg,
		"roll_deg": rad_to_deg(rot.x),
		"pitch_deg": rad_to_deg(rot.z),
		"yaw_deg": rad_to_deg(rot.y)
	}
	file.store_line(JSON.stringify(line))

func _exit_tree() -> void:
	stop_logging()
