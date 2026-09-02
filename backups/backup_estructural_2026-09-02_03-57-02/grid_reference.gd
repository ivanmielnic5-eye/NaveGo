extends Node3D

@export var grid_size: Vector2 = Vector2(10, 10)
@export var spacing: float = 50.0
@export var color: Color = Color(0.2, 0.6, 1.0, 0.3)

func _ready():
	_create_grid()

func _create_grid():
	for i in range(grid_size.x + 1):
		var x_pos = (i - grid_size.x / 2.0) * spacing
		var start = Vector3(x_pos, 0, -grid_size.y / 2.0 * spacing)
		var end = Vector3(x_pos, 0, grid_size.y / 2.0 * spacing)
		_create_line(start, end)

	for i in range(grid_size.y + 1):
		var z_pos = (i - grid_size.y / 2.0) * spacing
		var start = Vector3(-grid_size.x / 2.0 * spacing, 0, z_pos)
		var end = Vector3(grid_size.x / 2.0 * spacing, 0, z_pos)
		_create_line(start, end)

func _create_line(start: Vector3, end: Vector3):
	var mesh_instance = MeshInstance3D.new()
	var mesh = ImmediateMesh.new()
	mesh_instance.mesh = mesh
	add_child(mesh_instance)

	var material = StandardMaterial3D.new()
	material.albedo_color = color
	material.transparency = StandardMaterial3D.TRANSPARENCY_ALPHA
	material.shading_mode = StandardMaterial3D.SHADING_MODE_UNSHADED

	mesh.surface_begin(Mesh.PRIMITIVE_LINES, material)
	mesh.surface_add_vertex(start)
	mesh.surface_add_vertex(end)
	mesh.surface_end()
