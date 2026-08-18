// simulate.js
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 3000;
const SANDBOX_DIR = path.join(__dirname, 'sandbox');
const TRAJECTORY_FILE = path.join(SANDBOX_DIR, 'trajectory_data.json');
const HAZARDS_FILE = path.join(SANDBOX_DIR, 'hazards_data.json');

if (!fs.existsSync(SANDBOX_DIR)) {
  fs.mkdirSync(SANDBOX_DIR, { recursive: true });
}

const server = http.createServer((req, res) => {
  if (req.method === 'POST' && req.url === '/update-trajectory') {
    let body = '';
    req.on('data', (chunk) => {
      body += chunk.toString();
    });
    req.on('end', () => {
      try {
        const payload = JSON.parse(body);
        // Compatibilidad: si envía solo un array, lo tomamos como puntos
        const points = Array.isArray(payload) ? payload : payload.points || [];
        const hazards = (payload.hazards && Array.isArray(payload.hazards)) ? payload.hazards : [];

        fs.writeFileSync(TRAJECTORY_FILE, JSON.stringify(points, null, 2), 'utf8');
        fs.writeFileSync(HAZARDS_FILE, JSON.stringify(hazards, null, 2), 'utf8');

        console.log(`[MATRIS_BRIDGE] ÉXITO - ${points.length} puntos, ${hazards.length} peligros activos`);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true, count: points.length, hazards: hazards.length }));
      } catch (err) {
        console.error('[MATRIS_BRIDGE] Error al parsear JSON:', err);
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, error: err.message }));
      }
    });
  } else {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not found');
  }
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`[MATRIS_BRIDGE] Servidor escuchando en http://0.0.0.0:${PORT}`);
  console.log(`[MATRIS_BRIDGE] Trayectoria: ${TRAJECTORY_FILE}`);
  console.log(`[MATRIS_BRIDGE] Peligros: ${HAZARDS_FILE}`);
});