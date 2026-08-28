extends CanvasLayer

@export var capitania_path: NodePath
var capitania: Node = null

# Etiquetas
var label_gps: Label
var label_imu: Label
var label_wind: Label
var label_sync: Label
var label_sog: Label
var label_cog: Label
var label_hdg: Label
var label_pos: Label
var label_aws: Label
var label_awa: Label
var label_tws: Label
var label_twa: Label
var label_error: Label
var label_estado: Label

func _ready():
    capitania = get_node_or_null(capitania_path)
    if capitania == null:
        push_warning("[Cockpit] Capitania no encontrada.")
        return
    
    if capitania.has_signal("snapshot_emitted"):
        capitania.snapshot_emitted.connect(_on_snapshot)
        print("[Cockpit] Conectado a Capitania.")
    else:
        push_warning("[Cockpit] Capitania no tiene señal snapshot_emitted.")
    
    _setup_ui()

func _setup_ui():
    var color_fondo = Color(0.1, 0.1, 0.15, 0.9)
    var color_texto = Color.WHITE
    
    var panel = Panel.new()
    panel.size = Vector2(400, 600)
    panel.position = Vector2(10, 10)
    panel.color = color_fondo
    add_child(panel)
    
    var title = Label.new()
    title.text = "NAVEGO - COCKPIT"
    title.position = Vector2(20, 20)
    title.add_theme_color_override("font_color", Color.CYAN)
    panel.add_child(title)
    
    # Estado
    var label_estado_title = Label.new()
    label_estado_title.text = "ESTADO"
    label_estado_title.position = Vector2(20, 50)
    label_estado_title.add_theme_color_override("font_color", Color.YELLOW)
    panel.add_child(label_estado_title)
    
    label_gps = Label.new()
    label_gps.text = "GPS: --"
    label_gps.position = Vector2(30, 80)
    panel.add_child(label_gps)
    
    label_imu = Label.new()
    label_imu.text = "IMU: --"
    label_imu.position = Vector2(30, 100)
    panel.add_child(label_imu)
    
    label_wind = Label.new()
    label_wind.text = "WIND: --"
    label_wind.position = Vector2(30, 120)
    panel.add_child(label_wind)
    
    label_sync = Label.new()
    label_sync.text = "SYNC: --"
    label_sync.position = Vector2(30, 140)
    panel.add_child(label_sync)
    
    # Navegación
    var label_nav_title = Label.new()
    label_nav_title.text = "NAVEGACIÓN"
    label_nav_title.position = Vector2(20, 180)
    label_nav_title.add_theme_color_override("font_color", Color.YELLOW)
    panel.add_child(label_nav_title)
    
    label_sog = Label.new()
    label_sog.text = "SOG: --"
    label_sog.position = Vector2(30, 210)
    panel.add_child(label_sog)
    
    label_cog = Label.new()
    label_cog.text = "COG: --"
    label_cog.position = Vector2(30, 230)
    panel.add_child(label_cog)
    
    label_hdg = Label.new()
    label_hdg.text = "HDG: --"
    label_hdg.position = Vector2(30, 250)
    panel.add_child(label_hdg)
    
    label_pos = Label.new()
    label_pos.text = "POS: --"
    label_pos.position = Vector2(30, 270)
    panel.add_child(label_pos)
    
    # Viento
    var label_wind_title = Label.new()
    label_wind_title.text = "VIENTO"
    label_wind_title.position = Vector2(20, 310)
    label_wind_title.add_theme_color_override("font_color", Color.YELLOW)
    panel.add_child(label_wind_title)
    
    label_aws = Label.new()
    label_aws.text = "AWS: --"
    label_aws.position = Vector2(30, 340)
    panel.add_child(label_aws)
    
    label_awa = Label.new()
    label_awa.text = "AWA: --"
    label_awa.position = Vector2(30, 360)
    panel.add_child(label_awa)
    
    label_tws = Label.new()
    label_tws.text = "TWS: --"
    label_tws.position = Vector2(30, 380)
    panel.add_child(label_tws)
    
    label_twa = Label.new()
    label_twa.text = "TWA: --"
    label_twa.position = Vector2(30, 400)
    panel.add_child(label_twa)
    
    # Evidencia
    var label_evidencia_title = Label.new()
    label_evidencia_title.text = "EVIDENCIA"
    label_evidencia_title.position = Vector2(20, 440)
    label_evidencia_title.add_theme_color_override("font_color", Color.YELLOW)
    panel.add_child(label_evidencia_title)
    
    label_estado = Label.new()
    label_estado.text = "SISTEMA: --"
    label_estado.position = Vector2(30, 470)
    panel.add_child(label_estado)
    
    label_error = Label.new()
    label_error.text = "ERROR: --"
    label_error.position = Vector2(30, 490)
    panel.add_child(label_error)
    
    # Comandos
    var btn_start = Button.new()
    btn_start.text = "▶ START"
    btn_start.position = Vector2(30, 530)
    btn_start.size = Vector2(100, 30)
    btn_start.pressed.connect(_on_start)
    panel.add_child(btn_start)
    
    var btn_pause = Button.new()
    btn_pause.text = "⏸ PAUSE"
    btn_pause.position = Vector2(150, 530)
    btn_pause.size = Vector2(100, 30)
    btn_pause.pressed.connect(_on_pause)
    panel.add_child(btn_pause)

func _on_snapshot(snapshot: Dictionary):
    var nav = snapshot.get("navigation", {})
    if nav:
        if label_sog:
            label_sog.text = "SOG: %.1f kn" % nav.get("sog_knots", 0.0)
        if label_cog:
            if nav.get("cog_valid", false):
                label_cog.text = "COG: %03d°" % int(nav.get("cog_deg", 0.0))
            else:
                label_cog.text = "COG: NO VALIDO"
        if label_hdg:
            if nav.get("heading_valid", false):
                label_hdg.text = "HDG: %03d°" % int(nav.get("heading_deg", 0.0))
            else:
                label_hdg.text = "HDG: NO VALIDO"
    
    var wind = snapshot.get("wind", {})
    if wind:
        if label_aws:
            label_aws.text = "AWS: %.1f kn" % wind.get("aws_knots", 0.0)
        if label_awa:
            label_awa.text = "AWA: %03d°" % int(wind.get("awa_deg", 0.0))
        if label_tws:
            label_tws.text = "TWS: %.1f kn" % wind.get("tws_knots", 0.0)
        if label_twa:
            label_twa.text = "TWA: %03d°" % int(wind.get("twa_deg", 0.0))
    
    var pos = snapshot.get("position", {})
    if pos:
        if label_pos:
            label_pos.text = "POS: lat=%.4f lon=%.4f" % [pos.get("lat", 0.0), pos.get("lon", 0.0)]
    
    var sys = snapshot.get("system", {})
    if sys:
        if label_gps:
            label_gps.text = "GPS: %s" % sys.get("gps_quality", "UNKNOWN")
        if label_imu:
            label_imu.text = "IMU: OK"
        if label_wind:
            label_wind.text = "WIND: OK"
        if label_sync:
            label_sync.text = "SYNC: LOCAL"
        if label_estado:
            label_estado.text = "SISTEMA: %s" % ("OK" if sys.get("landscape_ok", false) else "ERROR")
        if label_error:
            label_error.text = "ERROR: %.2f m" % snapshot.get("error_m", 0.0)

func _on_start():
    if capitania:
        capitania.start_capture()

func _on_pause():
    if capitania:
        capitania.stop_capture()
