extends Camera3D

@export var objetivo_path: NodePath
@export var distancia: float = 20.0    # <-- cambia esto para acercar/alejar
@export var altura: float = 8.0        # <-- cambia esto para subir/bajar cámara
@export var suavidad: float = 2.0      # <-- delay: 0.5 lento, 5 rápido

var objetivo: Node3D = null
var pos_suave: Vector3 = Vector3.ZERO

func _ready():
	objetivo = get_node_or_null(objetivo_path)
	if objetivo:
		pos_suave = objetivo.global_position
		print("[Camara] Sigue a ", objetivo.name)

func _process(delta):
	if objetivo == null:
		return
	var objetivo_pos = objetivo.global_position
	# Suavizado: la cámara "persigue" la posición del barco con delay
	pos_suave = pos_suave.lerp(objetivo_pos, suavidad * delta)
	global_position = pos_suave + Vector3(0, altura, distancia)
	look_at(pos_suave, Vector3.UP)
