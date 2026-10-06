extends Node

# timonel_bridge.gd - Canal bidireccional Polaris <-> DSH
# Fase 1: solo timon.
# No toca scripts existentes. Si timonel.py no corre, no pasa nada.

@export var sailboat_path: NodePath
@export var telemetry_interval_s: float = 1.0
@export var command_read_interval_s: float = 0.5
@export var timon_torque: float = 2500.0
@export var timon_duration_ms: int = 3000
@export var avance_duration_ms: int = 5000
@export var avance_force: float = 6000.0

var sailboat: RigidBody3D = null
var heading_integrator: Node = null
var telemetry_file: FileAccess = null
var telemetry_path: String = ""
var command_path: String = ""

var _t_acc: float = 0.0
var _cmd_acc: float = 0.0
var _last_command_t: int = 0
var _last_timon: int = 0
var _last_avance: int = 0
var _timon_until_ms: int = 0
var _dist_anterior: float = -1.0
var _avance_until_ms: int = 0

func _ready() -> void:
    sailboat = get_node_or_null(sailboat_path) as RigidBody3D
    if sailboat == null:
        push_warning("[Timonel] Sailboat no encontrado.")
        return

    var dir_path := "user://timonel"
    DirAccess.make_dir_recursive_absolute(dir_path)
    telemetry_path = dir_path + "/telemetria.jsonl"
    command_path = dir_path + "/comandos.jsonl"

    telemetry_file = FileAccess.open(telemetry_path, FileAccess.WRITE)
    if telemetry_file == null:
        push_warning("[Timonel] No se pudo abrir telemetria.jsonl")
    else:
        print("[Timonel] Escribiendo telemetria en: ",
            ProjectSettings.globalize_path(telemetry_path))

    heading_integrator = get_tree().root.find_child("HeadingIntegrator", true, false)
    if heading_integrator == null:
        push_warning("[Timonel] HeadingIntegrator no encontrado.")
    else:
        print("[Timonel] HeadingIntegrator encontrado.")

    if not FileAccess.file_exists(command_path):
        var f := FileAccess.open(command_path, FileAccess.WRITE)
        if f != null:
            f.close()

func _process(delta: float) -> void:
    if sailboat == null or telemetry_file == null:
        return
    _t_acc += delta
    if _t_acc >= telemetry_interval_s:
        _t_acc = 0.0
        _write_telemetry()
    _cmd_acc += delta
    if _cmd_acc >= command_read_interval_s:
        _cmd_acc = 0.0
        _read_command()

func _write_telemetry() -> void:
    var pos := sailboat.global_position
    var vel := sailboat.linear_velocity
    var rot := sailboat.global_rotation
    var horizontal := Vector2(vel.x, vel.z)
    var sog_kn := horizontal.length() * 1.94384
    var cog_deg := 0.0
    if horizontal.length() > 0.05:
        cog_deg = fmod(rad_to_deg(atan2(vel.x, -vel.z)) + 360.0, 360.0)
    var forward := -sailboat.global_transform.basis.z
    var hdg_deg := fmod(rad_to_deg(atan2(forward.x, -forward.z)) + 360.0, 360.0)
    var aws_kn := 0.0
    var awa_deg := 0.0
    if heading_integrator != null and heading_integrator.has_method("get_navigation_snapshot"):
        var nav = heading_integrator.get_navigation_snapshot()
        aws_kn = nav.get("apparent_wind_speed_ms", 0.0) * 1.94384449
        awa_deg = nav.get("apparent_wind_angle_deg", 0.0)
    var meta_x := 36.0
    var meta_z := -6.0
    var dist_a_meta := sqrt(pow(pos.x - meta_x, 2) + pow(pos.z - meta_z, 2))
    var progreso := 0.0
    if _dist_anterior > 0.0:
        progreso = _dist_anterior - dist_a_meta
    _dist_anterior = dist_a_meta

    var line := {
        "t": int(Time.get_unix_time_from_system() * 1000),
        "pos_x": pos.x, "pos_y": pos.y, "pos_z": pos.z,
        "sog_kn": sog_kn, "cog_deg": cog_deg, "hdg_deg": hdg_deg,
        "aws_kn": aws_kn, "awa_deg": awa_deg,
        "dist_a_meta": dist_a_meta, "progreso": progreso,
        "roll_deg": rad_to_deg(rot.x),
        "pitch_deg": rad_to_deg(rot.z),
        "yaw_deg": rad_to_deg(rot.y)
    }
    telemetry_file.store_line(JSON.stringify(line))
    telemetry_file.flush()

func _read_command() -> void:
    if not FileAccess.file_exists(command_path):
        return
    var f := FileAccess.open(command_path, FileAccess.READ)
    if f == null:
        return
    var last_line := ""
    while not f.eof_reached():
        var l := f.get_line().strip_edges()
        if l != "":
            last_line = l
    f.close()
    if last_line == "":
        return
    var parsed = JSON.parse_string(last_line)
    if typeof(parsed) != TYPE_DICTIONARY:
        return
    var cmd_t: int = int(parsed.get("t", 0))
    if cmd_t <= _last_command_t:
        return
    _last_command_t = cmd_t
    _last_timon = int(parsed.get("timon", 0))
    _last_avance = int(parsed.get("avance", 0))
    var timon_ms: int = int(parsed.get("timon_ms", timon_duration_ms))
    var avance_ms: int = int(parsed.get("avance_ms", avance_duration_ms))
    var ahora_ms_cmd := int(Time.get_unix_time_from_system() * 1000)
    if _last_timon != 0:
        _timon_until_ms = ahora_ms_cmd + timon_ms
    if _last_avance != 0:
        _avance_until_ms = ahora_ms_cmd + avance_ms
    print("[Timonel] leido: t=%d timon=%d (%d ms) avance=%d (%d ms)" % [cmd_t, _last_timon, timon_ms, _last_avance, avance_ms])

func _physics_process(_delta: float) -> void:
    if sailboat == null:
        return
    var ahora_ms := int(Time.get_unix_time_from_system() * 1000)
    if _last_timon != 0 and ahora_ms <= _timon_until_ms:
        var torque_dir := -_last_timon
        sailboat.apply_torque(Vector3.UP * timon_torque * torque_dir)
    if _last_avance != 0 and ahora_ms <= _avance_until_ms:
        var forward := -sailboat.global_transform.basis.z
        sailboat.apply_central_force(forward * avance_force * _last_avance)

func _exit_tree() -> void:
    if telemetry_file != null:
        telemetry_file.close()
        telemetry_file = null
