const http = require("http");
const { exec } = require("child_process");

const commands = {
  "/guardar": "powershell.exe -ExecutionPolicy Bypass -File \"C:\\Users\\ivan\\Downloads\\_Proyectos\\NaveGoLocal\\save.ps1\"",
  "/arrancar": "powershell.exe -ExecutionPolicy Bypass -File \"C:\\Users\\ivan\\Downloads\\_Proyectos\\NaveGoLocal\\start.ps1\"",
  "/estado": "powershell.exe -ExecutionPolicy Bypass -File \"C:\\Users\\ivan\\Downloads\\_Proyectos\\NaveGoLocal\\estado.ps1\"",
  "/backup": "powershell.exe -ExecutionPolicy Bypass -File \"C:\\Users\\ivan\\Downloads\\_Proyectos\\NaveGoLocal\\backup.ps1\"",
};

const server = http.createServer((req, res) => {
  const command = commands[req.url];
  if (command) {
    exec(command, (error, stdout, stderr) => {
      res.writeHead(200, {"Content-Type": "text/plain; charset=utf-8"});
      res.end(stdout || stderr || "Ejecutado");
    });
  } else {
    res.writeHead(200, {"Content-Type": "text/plain; charset=utf-8"});
    res.end("LOGOS Voice Bridge activo. Comandos: /guardar /arrancar /estado /backup");
  }
});

server.listen(4000, () => console.log("LOGOS Voice Bridge en http://localhost:4000"));
