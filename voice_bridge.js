const http = require("http");
const { exec } = require("child_process");
const { URL } = require("url");
const fs = require("fs");

const TOKEN = "NAVEGO-2026-LOGOS";

const commands = {
  "/guardar": { script: "save.ps1", wait: true },
  "/estado": { script: "estado.ps1", wait: true },
  "/arrancar": { script: "start.ps1", wait: false },
  "/backup": { script: "backup.ps1", wait: false },
};

function ejecutar(path, wait, res) {
  const script = "powershell.exe -ExecutionPolicy Bypass -File \"C:\\Users\\ivan\\Downloads\\_Proyectos\\NaveGoLocal\\" + commands[path].script + "\"";
  if (wait) {
    exec(script, (error, stdout, stderr) => {
      res.writeHead(200, { "Content-Type": "text/plain; charset=utf-8" });
      res.end(stdout || stderr || "OK");
    });
  } else {
    exec(script);
    res.writeHead(200, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("Ejecutado en la PC");
  }
}

const html = fs.readFileSync(__dirname + "/panel.html", "utf8");

const server = http.createServer((req,res) => {
  const myUrl = new URL(req.url, "http://localhost");
  const path = myUrl.pathname;
  const token = myUrl.searchParams.get("token");

  if (path === "/") {
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    res.end(html);
    return;
  }

  if (token !== TOKEN) {
    res.writeHead(401, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("Token inválido o ausente.");
    return;
  }

  const command = commands[path];
  if (command) {
    ejecutar(path, command.wait, res);
  } else {
    res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("No encontrado");
  }
});

server.listen(4000, () => console.log("LOGOS Voice Bridge con token en http://localhost:4000"));
