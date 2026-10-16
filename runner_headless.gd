extends Node

# ============================================================
# RUNNER HEADLESS — Orquestador de experimentos en headless
# ============================================================
# Solo actúa si NAVEGO_RUN_DIR está exportada.
# Si no está, no hace nada (comportamiento normal del simulador).

var _activo: bool = false
var _run_dir: String = ""
var _comandos: Array = []
var _duracion_total_ms: int = 0
var _grace_ms: int = 2000
var _idx_comando: int = 0
var _t_inicio_unix_ms: int = 0
var _t_inicio_ticks_ms: int = 0
var _timeout_ms: int = 120000
var _cmd_file: FileAccess = null
var _log_file: FileAccess = null
var _ultimo_cmd_rel_ms: int = 0
var _ultimo_cmd_aplicado_ms: int = 0
var _comandos_escritos: int = 0

const MIN_SPACING_MS := 600

func _ready() -> void:
	_run_dir = OS.get_environment("NAVEGO_RUN_DIR")
	if _run_dir == "":
		return
	_activo = true
	_iniciar()

func _iniciar() -> void:
	var log_path := _run_dir + "/runner.log"
	_log_file = FileAccess.open(log_path, FileAccess.WRITE)
	if _log_file == null:
		push_error("[runner] No se pudo abrir runner.log")
		get_tree().quit(2)
		return

	_log("inicio " + Time.get_datetime_string_from_system())
	_log("run_dir=" + _run_dir)

	if FileAccess.file_exists(_run_dir + "/comandos.jsonl") and _file_no_vacio(_run_dir + "/comandos.jsonl"):
		_log("ERROR: comandos.jsonl ya existe y no esta vacio")
		_cerrar(3, "archivo_residual")
		return
	if FileAccess.file_exists(_run_dir + "/ground_truth.jsonl") and _file_no_vacio(_run_dir + "/ground_truth.jsonl"):
		_log("ERROR: ground_truth.jsonl ya existe y no esta vacio")
		_cerrar(3, "archivo_residual")
		return

	var input_path := _run_dir + "/comandos_in.json"
	if not FileAccess.file_exists(input_path):
		_log("ERROR: comandos_in.json no existe")
		_cerrar(2, "input_faltante")
		return

	var f := FileAccess.open(input_path, FileAccess.READ)
	if f == null:
		_log("ERROR: no se pudo abrir comandos_in.json")
		_cerrar(2, "input_inaccesible")
		return
	var contenido := f.get_as_text()
	f.close()

	var parsed = JSON.parse_string(contenido)
	if typeof(parsed) != TYPE_DICTIONARY:
		_log("ERROR: comandos_in.json no es objeto JSON valido")
		_cerrar(2, "input_invalido")
		return

	var error_validacion := _validar_input(parsed)
	if error_validacion != "":
		_log("ERROR de validacion: " + error_validacion)
		_cerrar(2, "validacion_fallida")
		return

	_duracion_total_ms = int(parsed.get("duracion_total_ms", 0))
	_grace_ms = int(parsed.get("grace_ms", 2000))
	_comandos = parsed.get("comandos", [])

	_log("comandos_in cargados: %d" % _comandos.size())
	_log("validacion OK")

	_cmd_file = FileAccess.open(_run_dir + "/comandos.jsonl", FileAccess.WRITE)
	if _cmd_file == null:
		_log("ERROR: no se pudo abrir comandos.jsonl")
		_cerrar(2, "output_inaccesible")
		return

	_t_inicio_unix_ms = int(Time.get_unix_time_from_system() * 1000)
	_t_inicio_ticks_ms = Time.get_ticks_msec()

	_log("t_inicio unix=%d ticks=%d" % [_t_inicio_unix_ms, _t_inicio_ticks_ms])
	_log("duracion_total_ms=%d grace_ms=%d timeout_ms=%d" % [_duracion_total_ms, _grace_ms, _timeout_ms])

func _validar_input(parsed: Dictionary) -> String:
	if not parsed.has("duracion_total_ms"):
		return "falta duracion_total_ms"
	var dur := int(parsed.get("duracion_total_ms", 0))
	if dur <= 0:
		return "duracion_total_ms debe ser > 0"

	if not parsed.has("comandos"):
		return "falta comandos"
	var cmds = parsed.get("comandos", [])
	if typeof(cmds) != TYPE_ARRAY or cmds.size() == 0:
		return "comandos debe ser array con al menos 1 elemento"

	var t_prev := -1
	for i in range(cmds.size()):
		var c = cmds[i]
		if typeof(c) != TYPE_DICTIONARY:
			return "comando %d no es objeto" % i
		if not c.has("t_relativo_ms"):
			return "comando %d sin t_relativo_ms" % i
		var t_rel := int(c.get("t_relativo_ms", 0))
		if t_rel < 0 or t_rel > dur:
			return "comando %d t_relativo_ms fuera de rango" % i
		if t_rel <= t_prev:
			return "comando %d no es ascendente" % i
		if t_prev >= 0 and (t_rel - t_prev) < MIN_SPACING_MS:
			return "comando %d a menos de %d ms del anterior" % [i, MIN_SPACING_MS]
		t_prev = t_rel

		if not c.has("timon") or not c.has("avance"):
			return "comando %d sin timon o avance" % i
		var tim := int(c.get("timon", 0))
		var ava := int(c.get("avance", 0))
		if tim not in [-1, 0, 1]:
			return "comando %d timon fuera de rango" % i
		if ava not in [-1, 0, 1]:
			return "comando %d avance fuera de rango" % i

		var tim_ms := int(c.get("timon_ms", 0))
		var ava_ms := int(c.get("avance_ms", 0))
		if tim != 0 and (tim_ms <= 0 or tim_ms > 30000):
			return "comando %d timon_ms invalido" % i
		if ava != 0 and (ava_ms <= 0 or ava_ms > 30000):
			return "comando %d avance_ms invalido" % i

	return ""

func _process(_delta: float) -> void:
	if not _activo:
		return

	var ticks_actual := Time.get_ticks_msec()
	if ticks_actual - _t_inicio_ticks_ms > _timeout_ms:
		_log("TIMEOUT de pared superado %d ms" % (ticks_actual - _t_inicio_ticks_ms))
		_cerrar(1, "timeout")
		return

	var now_ms := int(Time.get_unix_time_from_system() * 1000)
	var t_rel_actual := now_ms - _t_inicio_unix_ms

	while _idx_comando < _comandos.size():
		var c = _comandos[_idx_comando]
		var t_cmd := int(c.get("t_relativo_ms", 0))
		if t_cmd > t_rel_actual:
			break
		_escribir_comando(c, t_cmd)
		_ultimo_cmd_rel_ms = t_cmd
		var dur_max: int = max(int(c.get("timon_ms", 0)), int(c.get("avance_ms", 0)))
		_ultimo_cmd_aplicado_ms = t_cmd + dur_max
		_idx_comando += 1

	if _idx_comando >= _comandos.size():
		var t_cierre_min := _ultimo_cmd_aplicado_ms + _grace_ms
		var t_cierre: int = max(t_cierre_min, _duracion_total_ms)
		if t_rel_actual >= t_cierre:
			_log("completitud alcanzada t_rel=%d" % _ultimo_cmd_rel_ms)
			_log("cierre por duracion total t_rel=%d min=%d dur=%d" % [t_rel_actual, t_cierre_min, _duracion_total_ms])
			_cerrar(0, "duracion_total")

func _escribir_comando(c: Dictionary, t_cmd: int) -> void:
	var now_ms := int(Time.get_unix_time_from_system() * 1000)
	var entry := {
		"t": now_ms,
		"timon": int(c.get("timon", 0)),
		"timon_ms": int(c.get("timon_ms", 0)),
		"avance": int(c.get("avance", 0)),
		"avance_ms": int(c.get("avance_ms", 0)),
		"fuente": "runner",
		"nota": "t_rel=%d" % t_cmd
	}
	_cmd_file.store_line(JSON.stringify(entry))
	_cmd_file.flush()
	_comandos_escritos += 1
	_log("comando %d escrito: t_rel=%d" % [_comandos_escritos, t_cmd])

func _cerrar(codigo: int, causa: String) -> void:
	_activo = false
	if _cmd_file != null:
		_cmd_file.close()
		_cmd_file = null

	var ticks_total := Time.get_ticks_msec() - _t_inicio_ticks_ms
	var resultado := {
		"run_id": _run_dir.get_file(),
		"exito_inicializacion": _comandos_escritos > 0 or _idx_comando == 0,
		"exito_ejecucion": codigo == 0,
		"causa_cierre": causa,
		"codigo_salida": codigo,
		"ticks_total_ms": ticks_total,
		"comandos_escritos": _comandos_escritos,
		"comandos_totales": _comandos.size()
	}
	var rf := FileAccess.open(_run_dir + "/resultado.json", FileAccess.WRITE)
	if rf != null:
		rf.store_string(JSON.stringify(resultado, "  "))
		rf.close()

	_log("cierre codigo=%d causa=%s ticks_total=%d" % [codigo, causa, ticks_total])
	if _log_file != null:
		_log_file.close()
		_log_file = null

	get_tree().quit(codigo)

func _log(msg: String) -> void:
	if _log_file != null:
		_log_file.store_line("[runner] " + msg)
		_log_file.flush()

func _file_no_vacio(path: String) -> bool:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return false
	var n := f.get_length()
	f.close()
	return n > 0
