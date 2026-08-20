const http = require("http");
const { exec } = require("child_process");

const server = http.createServer((req, res) => {
  if (req.url === "/guardar") {
    exec("powershell.exe -ExecutionPolicy Bypass -File \"C:\\Users\\ivan\\Downloads\\_Proyectos\\NaveGoLocal\\save.ps1\"", (error, stdout, stderr) => {
      res.writeHead(200, {"Content-Type": "text/plain; charset=utf-8"});
      res.end(stdout || stderr || "Guardado");
    });
  } else {
    res.writeHead(200, {"Content-Type": "text/plain; charset=utf-8"});
    res.end("NaveGo Voice Bridge activo. Usá /guardar");
  }
});

server.listen(4000, () => console.log("Voice bridge en http://localhost:4000"));
