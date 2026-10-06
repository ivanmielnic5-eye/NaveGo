extends Node

@export var sailboat_path: NodePath
@export var cam1_path: NodePath  # Picado (aerea inclinada)
@export var cam2_path: NodePath  # Cenital (arriba mirando abajo)
@export var cam3_path: NodePath  # Lateral derecha
@export var cam4_path: NodePath  # Subjetiva (en el barco)
@export var cam5_path: NodePath  # Lateral izquierda (cerca del muelle)
@export var cam6_path: NodePath  # Fija cenital sobre Puerto Esperanza

var sailboat: Node3D = null
var cameras: Array = []

const OFFSET_PICADO       = Vector3(0, 14, 12)
const OFFSET_CENITAL      = Vector3(0, 22, 0.03)
const OFFSET_LATERAL_DER  = Vector3(22, 8, 0)
const OFFSET_SUBJETIVA    = Vector3(-1, 3, 4)
const OFFSET_LATERAL_IZQ  = Vector3(-22, 8, 0)

func _ready():
    sailboat = get_node_or_null(sailboat_path)
    cameras = [
        get_node_or_null(cam1_path),
        get_node_or_null(cam2_path),
        get_node_or_null(cam3_path),
        get_node_or_null(cam4_path),
        get_node_or_null(cam5_path),
        get_node_or_null(cam6_path),
    ]
    if sailboat == null:
        push_warning("[CameraSwitcher] Sailboat no encontrado.")
        return
    if cameras[0]:
        cameras[0].make_current()
    print("[CameraSwitcher] Activo. Teclas 1-6.")

func _process(_delta):
    if sailboat == null:
        return
    var boat_pos = sailboat.global_position

    if cameras[0]:
        cameras[0].global_position = boat_pos + OFFSET_PICADO
        cameras[0].look_at(boat_pos, Vector3.UP)
    if cameras[1]:
        cameras[1].global_position = boat_pos + OFFSET_CENITAL
        cameras[1].look_at(boat_pos, Vector3.UP)
    if cameras[2]:
        cameras[2].global_position = boat_pos + OFFSET_LATERAL_DER
        cameras[2].look_at(boat_pos, Vector3.UP)
    if cameras[3]:
        var boat_transform = sailboat.global_transform
        cameras[3].global_position = boat_transform * Vector3(-1, 3, 4)
        var fwd4 = -boat_transform.basis.z
        var look4 = cameras[3].global_position + fwd4 * 100 - Vector3(0, 20, 0)
        cameras[3].look_at(look4, Vector3.UP)
    if cameras[4]:
        cameras[4].global_position = boat_pos + OFFSET_LATERAL_IZQ
        cameras[4].look_at(boat_pos, Vector3.UP)
    # Cam 6: FIJA sobre Puerto Esperanza. No sigue al barco.
    if cameras[5]:
        # Muelle actual: (36, 2, -6). Apuntamos al deck visible (4m sobre el origen).
        var cine_target = Vector3(18, 4, -3)
        # Camara 25m al sur del muelle, 12m arriba.
        cameras[5].global_position = Vector3(-5, 18, -35)
        cameras[5].look_at(cine_target, Vector3.UP)

func _input(event):
    if event is InputEventKey and event.pressed and not event.echo:
        match event.keycode:
            KEY_1: _activar(0)
            KEY_2: _activar(1)
            KEY_3: _activar(2)
            KEY_4: _activar(3)
            KEY_5: _activar(4)
            KEY_6: _activar(5)

func _activar(idx: int):
    if idx < cameras.size() and cameras[idx]:
        cameras[idx].make_current()
        print("[CameraSwitcher] Camara ", idx + 1, " activa.")
