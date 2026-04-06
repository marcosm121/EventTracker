# EventTracker

API de tracking de eventos construida con FastAPI y MongoDB Atlas. Permite a clientes con API key enviar eventos arbitrarios para ser almacenados de forma aislada por cliente.

## Arquitectura

```
Cliente → POST /event (Authorization: <api_key>)
        → Rate limiting (por tier)
        → Validación de API key en MongoDB
        → Enriquecimiento del evento (client_ip)
        → Inserción en colección exclusiva del cliente
```

Cada API key tiene asociado un `col_id` único, que determina la colección de MongoDB donde se guardan sus eventos. Esto aísla los datos entre clientes.

## Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/` | Health check | No |
| POST | `/event` | Trackea un evento | Si (API key) |
| GET | `/generate` | Genera una API key premium | Si (Admin key) |

### POST /event

Recibe cualquier JSON en el body. El servidor agrega automáticamente el campo `client_ip` antes de persistir el evento.

**Header requerido:**
```
Authorization: <api_key>
```

**Ejemplo de body:**
```json
{
  "event": "user_signup",
  "user_id": "123",
  "timestamp": "2026-04-05T10:00:00Z"
}
```

### GET /generate

Genera una nueva API key con tier premium y la persiste en MongoDB. Requiere autenticación mediante admin key.

**Header requerido:**
```
X-Admin-Key: <ADMIN_KEY>
```

**Respuesta:**
```
"xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

La key devuelta es la que el cliente debe usar en el header `Authorization` para llamar a `/event`.

## Rate Limiting

El rate limiting se aplica por API key, con una ventana deslizante de 60 segundos.

| Tier | Requests por minuto |
|------|---------------------|
| premium | 50 RPM |
| freemium | 5 RPM |

> El estado del rate limit es in-memory: se resetea al reiniciar el servicio.

## Estructura del proyecto

```
EventTracker/
├── main.py                  # FastAPI app, middleware de logging, rate limiting
├── authenticator/
│   └── authManager.py       # Validación y generación de API keys
├── eventer/
│   └── eventManager.py      # Inserción de eventos
├── mongo/
│   └── mongoManager.py      # Clientes MongoDB (auth, logs, eventos)
├── models/
│   └── models.py            # Modelos Pydantic
├── requirements.txt
└── dockerfile
```

## MongoDB

Usa dos bases de datos:

- `service.apikeys` — API keys con su tier y col_id asociado
- `service.logs` — Log de todos los requests (método, path, body, tiempo de proceso)
- `events.<col_id>` — Colección de eventos por cliente

## Configuración

Variables de entorno requeridas (via `.env`):

```
MONGO_URL=<usuario>:<password>@<host>
ADMIN_KEY=<secret>
```

## Correr con Docker

```bash
docker build -t eventtracker .
docker run -p 8000:0000 --env-file .env eventtracker
```

## Correr en local

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Notas

- **Rate limiting in-memory**: el conteo de requests por API key se guarda en memoria del proceso. Si el servicio corre con múltiples workers o se reinicia, el contador se resetea. Para producción habría que usar un store compartido (ej. Redis).
- **CORS abierto**: la API acepta requests de cualquier origen (`*`). Está pensado para facilitar la integración durante desarrollo; en un entorno productivo convendría restringirlo a los orígenes conocidos.
- **Logs guardan el body completo**: cada request queda registrado en MongoDB incluyendo el body. Si se procesan datos sensibles, habría que filtrar o sanitizar antes de persistir.
