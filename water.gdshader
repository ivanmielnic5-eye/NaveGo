shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_burley, specular_schlick_ggx;

uniform float water_level = 0.0;

uniform float wave1_amplitude = 0.5;
uniform float wave1_wavelength = 30.0;
uniform float wave1_dir_deg = 90.0;
uniform float wave1_speed = 3.0;

uniform float wave2_amplitude = 0.25;
uniform float wave2_wavelength = 18.0;
uniform float wave2_dir_deg = 135.0;
uniform float wave2_speed = 2.2;

uniform float wave3_amplitude = 0.15;
uniform float wave3_wavelength = 12.0;
uniform float wave3_dir_deg = 45.0;
uniform float wave3_speed = 1.8;

uniform float wave4_amplitude = 0.08;
uniform float wave4_wavelength = 6.0;
uniform float wave4_dir_deg = 200.0;
uniform float wave4_speed = 1.2;

uniform float wave_time = 0.0;
uniform vec3 shallow_color : source_color = vec3(0.15, 0.35, 0.6);
uniform vec3 deep_color : source_color = vec3(0.05, 0.15, 0.35);

varying vec3 world_pos;

float wave_height(vec2 p) {
	float h = water_level;
	vec2 d1 = vec2(cos(radians(wave1_dir_deg)), sin(radians(wave1_dir_deg)));
	vec2 d2 = vec2(cos(radians(wave2_dir_deg)), sin(radians(wave2_dir_deg)));
	vec2 d3 = vec2(cos(radians(wave3_dir_deg)), sin(radians(wave3_dir_deg)));
	vec2 d4 = vec2(cos(radians(wave4_dir_deg)), sin(radians(wave4_dir_deg)));
	float k1 = TAU / wave1_wavelength;
	float k2 = TAU / wave2_wavelength;
	float k3 = TAU / wave3_wavelength;
	float k4 = TAU / wave4_wavelength;
	h += wave1_amplitude * sin(k1 * dot(p, d1) - k1 * wave1_speed * wave_time);
	h += wave2_amplitude * sin(k2 * dot(p, d2) - k2 * wave2_speed * wave_time);
	h += wave3_amplitude * sin(k3 * dot(p, d3) - k3 * wave3_speed * wave_time);
	h += wave4_amplitude * sin(k4 * dot(p, d4) - k4 * wave4_speed * wave_time);
	return h;
}

void vertex() {
	vec4 world = MODEL_MATRIX * vec4(VERTEX, 1.0);
	world_pos = world.xyz;
	float h = wave_height(world.xz);
	VERTEX.y = h - MODEL_MATRIX[3][1];
	float eps = 0.5;
	float h_x = wave_height(world.xz + vec2(eps, 0.0));
	float h_z = wave_height(world.xz + vec2(0.0, eps));
	float dh_dx = (h_x - h) / eps;
	float dh_dz = (h_z - h) / eps;
	NORMAL = normalize(vec3(-dh_dx, 1.0, -dh_dz));
}

void fragment() {
	float height_norm = clamp((world_pos.y + 0.5) * 0.7, 0.0, 1.0);
	vec3 col = mix(deep_color, shallow_color, height_norm);
	vec3 V = normalize(VIEW);
	float fresnel = pow(1.0 - max(0.0, dot(V, NORMAL)), 3.0);
	ALBEDO = mix(col, vec3(0.7, 0.85, 1.0), fresnel * 0.6);
	ALPHA = 0.92;
	ROUGHNESS = 0.15;
	METALLIC = 0.0;
	SPECULAR = 0.5;
}
