# Transcripción 03 — Infraestructura y Backend

Fuente: Curso "Crear una aplicación con inteligencia artificial" (Anthony Souza / HOTMARK)
Fecha de subida: 2026-09-15
Tema: Infraestructura, backend y costos de servicios

## Notas clave

### Estructura de una app
- Frontend (la app del celular)
- Backend (servicios, datos, lógica)

### Servicios mencionados por el autor

| Servicio | Rol | Costo |
|----------|-----|-------|
| Railway | Backend (deploy) | Prueba 30 días gratis |
| Supabase | Base de datos | Gratis hasta cierto punto |
| AWS | Backend/infra | Pago |
| Vercel | Landing page | Gratis |
| Cloudflare | Protección API (anti-DoS, anti-bots) | Gratis |
| Expo / EAS | Build de la app | Gratis con opciones Pro (USD 9/mes) |
| GitHub | Repositorio | Gratis |

### Dominio
- Comprar dominio propio (ej. cargoapp.lat).
- Alternativa: dominios .com más caros, .lat o .io más baratos.
- El dominio puede incluir email custom (contacto@cargoapp.com).

### Estrategia del autor
- Abaratar costos al máximo.
- Probar MVPs rápido, escalar si funciona, descartar si no.

### Relevancia para NaveGo
- NaveGo prioriza soberanía: backend propio en la Mini PC (R2-D2).
- No depende de Railway/Supabase/AWS.
- Los costos son casi cero (todo local).
- El único costo real podría ser el dominio si se publica.
