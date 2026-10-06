extends Node

const BRIDGE_URL = "http://127.0.0.1:11434/api/generate"

var http_request: HTTPRequest

func _ready() -> void:
	http_request = HTTPRequest.new()
	add_child(http_request)
	http_request.request_completed.connect(_on_request_completed)
	enviar_comando("Abrir YouTube")

func enviar_comando(prompt_texto: String) -> void:
	var headers = ["Content-Type: application/json"]
	var payload = {
		"model": "llama3",
		"system": "Eres un traductor de intenciones estricto. Tu única función es leer la orden del usuario y devolver UN ÚNICO objeto JSON válido que cumpla exactamente con este formato: {\"intent\": \"ACCION\", \"target\": \"OBJETIVO\", \"parameters\": {}, \"confidence\": 0.0}. No agregues texto adicional, explicaciones ni saludos.",
		"prompt": prompt_texto,
		"stream": false,
		"format": "json"
	}
	var body = JSON.stringify(payload)
	var error = http_request.request(BRIDGE_URL, headers, HTTPClient.METHOD_POST, body)
	if error != OK:
		print("[ERROR DE RED]: No se pudo disparar la petición HTTP.")

func _on_request_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray) -> void:
	if response_code != 200:
		print("[ERROR HTTP]: Código de estado ", response_code)
		return

	var json = JSON.new()
	var parse_error = json.parse(body.get_string_from_utf8())
	if parse_error != OK:
		print("[ERROR PARSER]: JSON raíz inválido.")
		return

	var response_data = json.get_data()
	var raw_response = response_data.get("response", "{}")

	# Parsear el JSON interno generado por el modelo
	var intent_json = JSON.new()
	if intent_json.parse(raw_response) == OK:
		var intent_data = intent_json.get_data()
		print("--- CONTRATO INTENTO CAPTURADO ---")
		print("Intent:      ", intent_data.get("intent"))
		print("Target:      ", intent_data.get("target"))
		print("Parameters:  ", intent_data.get("parameters"))
		print("Confidence:  ", intent_data.get("confidence"))
		print("---------------------------------")
	else:
		print("[RAW RESPONSE]: ", raw_response)
