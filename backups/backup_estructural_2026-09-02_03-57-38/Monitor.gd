extends Node

@export var sailboat_path: NodePath
@export var heading_integrator_path: NodePath

var sailboat: RigidBody3D = null
var heading_integrator: Node = null
var label: Label = null
var _time: float = 0.0
var _debug_counter: int = 0

func _ready():
	sailboat = get_node_or_null(sailboat_path) as RigidBody3D
	heading_integrator = get_node_or_null(heading_integrator_path)

	if sailboat == null:
		push_warning("[Monitor] Sailboat no encontrado.")
	if heading_integrator == null:
		push_warning("[Monitor] HeadingIntegrator no encontrado.")

	print("[Monitor NaveGo] Activo. Mostrando datos en pantalla (modo completo).")

	var canvas = CanvasLayer.new()
	add_child(canvas)

	label = Label.new()
	label.position = Vector2(20, 20)
	label.add_theme_font_size_override("font_size", 24)
	label.add_theme_color_override("font_color", Color(0.0, 1.0, 0.5))
	canvas.add_child(label)

func _process(delta):
	_time += delta
	_debug_counter += 1

	# ---- DATOS DE NAVEGACIÓN (RigidBody) ----
	var sog_kn = 0.0
	var cog_deg = 0.0
	var hdg_deg = 0.0
	var aws_kn = 0.0
	var awa_deg = 0.0

	if sailboat != null:
		# SOG y COG desde la velocidad lineal
		var velocity = sailboat.linear_velocity
		var horizontal = Vector2(velocity.x, velocity.z)
		var speed_ms = horizontal.length()
		if speed_ms > 0.05:
			sog_kn = speed_ms * 1.94384449
			var angle_rad = atan2(velocity.x, -velocity.z)
			cog_deg = fmod(rad_to_deg(angle_rad) + 360.0, 360.0)

		# HDG desde la orientación del barco
		var basis = sailboat.global_transform.basis
		var forward = -basis.z
		var heading_rad = atan2(forward.x, -forward.z)
		hdg_deg = fmod(rad_to_deg(heading_rad) + 360.0, 360.0)

	# ---- VIENTO DESDE HEADING INTEGRATOR ----
	if heading_integrator != null and heading_integrator.has_method("get_navigation_snapshot"):
		var nav = heading_integrator.get_navigation_snapshot()
		# Solo usamos el viento aparente desde el integrador
		aws_kn = nav.get("apparent_wind_speed_ms", 0.0) * 1.94384449
		awa_deg = nav.get("apparent_wind_angle_deg", 0.0)

		# Si el viento aparente es muy bajo, lo mostramos como 0
		if aws_kn < 0.5:
			aws_kn = 0.0
			awa_deg = 0.0

	# ---- INDICADOR DE NORTE ----
	var norte = "⬆ N" if int(hdg_deg) == 0 else ""

	# ---- DEBUG EN CONSOLA (cada 60 frames) ----
	if _debug_counter % 60 == 0:
		print("[Monitor] SOG: %.1f kn, COG: %03d°, HDG: %03d°, AWS: %.1f kn, AWA: %03d°" % [sog_kn, int(cog_deg), int(hdg_deg), aws_kn, int(awa_deg)])

	# ---- MOSTRAR EN PANTALLA ----
	label.text = "SOG: %.1f kn\nCOG: %03d°\nHDG: %03d° %s\nAWS: %.1f kn\nAWA: %03d°" % [sog_kn, int(cog_deg), int(hdg_deg), norte, aws_kn, int(awa_deg)]
