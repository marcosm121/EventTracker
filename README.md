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
| GET | `/generate` | Genera una API key premium | No |

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
