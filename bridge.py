import http.server
import socketserver
import json
import os

PORT = 8084
STATE_FILE = "/home/ivan/navego_state.json"

class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

class NavigationBridgeHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r") as f:
                    content = f.read()
                self.wfile.write(content.encode("utf-8"))
            except Exception as e:
                error_msg = json.dumps({"valid": 0, "error": str(e)})
                self.wfile.write(error_msg.encode("utf-8"))
        else:
            fallback = json.dumps({"valid": 0, "status": "waiting_for_daemon"})
            self.wfile.write(fallback.encode("utf-8"))

    def log_message(self, format, *args):
        return

if __name__ == "__main__":
    with ThreadingTCPServer(("", PORT), NavigationBridgeHandler) as httpd:
        print(f"[BRIDGE] Puente HTTP activo en puerto {PORT} consumiendo {STATE_FILE}")
        httpd.serve_forever()
