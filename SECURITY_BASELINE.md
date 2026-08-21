# SECURITY BASELINE — LOGOS / NaveGo

Actualizado: 2026-08-21

## Filosofia
First Offline: soberania de datos y operacion local absoluta.
La conectividad es opcional, controlada y nunca compromete la integridad.

## Nodo 1 — Seguridad en SQLite Local-First

### Opciones evaluadas
A. SQLCipher: cifrado total de la base. Alto impacto, migracion compleja.
B. Cifrado de campos sensibles con AES y claves en expo-secure-store. Bajo impacto.
C. Cifrado por sistema operativo. Depende del hardware.
D. Combinacion B + migracion futura a A. Progresivo y reversible.

### Recomendacion preliminar
Adoptar opcion D: empezar con cifrado de campos sensibles, mantener expo-sqlite.

## Nodo 2 — Perimetro de Red y Conectividad Hibrida

### Opciones evaluadas
A. Token de acceso en cada request. Simple y compatible.
B. Bind a localhost + reverse proxy. Reduce superficie de ataque.
C. Tunnel autenticado (cloudflared o ngrok). Mas robusto, requiere cuenta.
D. Firewall de Windows + IP fija. Bajo codigo pero fragil.
E. TLS local con certificados autofirmados. Cifra el canal.

### Recomendacion preliminar
1. Implementar token ahora (A).
2. Bind a localhost + proxy a mediano plazo (B).
3. Tunnel autenticado cuando se necesite exposicion remota real (C).

## Nodo 3 — Integridad del Pipeline

### Opciones evaluadas
A. Archivo de hashes SHA-256 antes de ejecutar scripts. Simple.
B. Firmado de scripts PowerShell con certificado. Profesional.
C. Git + GPG para trazabilidad. No impide alteracion local.
D. Watchdog de integridad con cuarentena. Proactivo.
E. Combinacion A + C. Robusto y modular.

### Recomendacion preliminar
Adoptar opcion E: hashes para ejecucion y Git/GPG para trazabilidad.

## Aporte creativo y de frontera
1. Inmunidad local: watchdog que detecta, aisla y notifica modificaciones.
2. Separacion por contenedores ligeros: cada adapter con permisos restringidos.
3. Handshake por doble canal: token + clave de sesion rotativa.
4. Cadena de confianza por hardware: secreto unico del dispositivo fisico.

## Decisiones pendientes del Director
- Confirmar opcion D para Nodo 1.
- Confirmar secuencia A-B-C para Nodo 2.
- Confirmar opcion E para Nodo 3.
- Definir si se implementa watchdog en fase posterior.

## Proximos pasos
1. Validar decisiones y actualizar este documento.
2. Implementar token en voice_bridge.js y simulate.js.
3. Generar primer integrity.json con hashes de scripts criticos.
4. Crear procedimiento de verificacion y rollback.

## Lista de scripts criticos
- start.ps1
- save.ps1
- backup.ps1
- estado.ps1
- voice_bridge.js
- simulate.js
