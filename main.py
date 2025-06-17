from fastapi import FastAPI, HTTPException, Request, Response
from models.models import logModel
from dotenv import load_dotenv
from typing import Any, Callable
from functools import wraps
from authenticator.authManager import authManager
from mongo.mongoManager import mongoLogManager
from eventer.eventManager import eventManager
from fastapi.middleware.cors import CORSMiddleware
import time
import json

load_dotenv()

app = FastAPI()
authenticator = authManager()
mongoLog = mongoLogManager()
eventManager = eventManager()

# Lista de orígenes permitidos
origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# Logging middleware
@app.middleware("logger")
async def log_request(request: Request, call_next):

    start_time = time.time()
    req_type = request.method
    path = request.url.path
    try:
        req_body = await request.json()
    except:
        req_body = {}

    response: Response = await call_next(request)
    
    process_time = time.time() - start_time


    try:
        log = logModel(req_type=req_type,path=path,req_body=str(req_body),process_time=process_time)

    except Exception as err:
        raise HTTPException(status_code=400, detail=f"Invalid arguments for log: {err}")

    try:
        # result = await requester.post_log(log)
        result = mongoLog.insert_entry(log)
        print(result)
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Error al loggear: {err}" )

    return response


# Decorador para la/s rutas
def rate_limit():
    def decorator(func: Callable[[Request], Any]) -> Callable[[Request], Any]:
        usage: dict[str, list[float]] = {}

        @wraps(func)
        async def wrapper(request: Request) -> Any:
            # get the API key
            authorization = request.headers.get('Authorization')

            if not authorization:
                raise HTTPException(status_code=401, detail="Header 'Authorization' is missing")

            # check if the API key is valid
            tier = authenticator.validate_key(authorization)
            # tier = await requester.get_auth(authorization)
            if tier == 'premium':
                rpm = 50
            elif tier == 'freemium':
                rpm = 5
            else:
                raise HTTPException(status_code=403, detail="Invalid API key")

            # update the timestamps
            now = time.time()
            if authorization not in usage:
                usage[authorization] = []
            timestamps = usage[authorization]
            timestamps[:] = [t for t in timestamps if now - t < 60]

            if len(timestamps) < rpm:
                timestamps.append(now)
                return await func(request)

            # calculate the time to wait before the next request
            wait = 60 - (now - timestamps[0])
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Retry after {wait:.2f} seconds",
            )

        return wrapper

    return decorator



@app.get("/")
def health():
    return {"message": "API Gateway funcionando correctamente"}

@app.post("/event")
@rate_limit()
async def service(request: Request):
    api_key = request.headers.get('Authorization')
    body_bytes = await request.body()  # Obtiene el body en bytes
    body_str = body_bytes.decode("utf-8")  # Convierte a string
    event = json.loads(body_str)
    event['client_ip'] = get_client_ip(request)
    try:
        # score = await requester.get_score(inputs)
        coleccion = authenticator.get_coleccion(api_key)
        eventManager.track_event(event, coleccion)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error llamando model: {e}")

    return f'Insertado en coleccion {coleccion}'


@app.get("/generate")
async def generate_key():
    data = authenticator.generate_key("premium")
    return data


# FUNCIONES AUXILIARES
def get_client_ip(request: Request) -> str:
    # Verifica X-Forwarded-For primero
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Fallback a X-Real-IP
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Si no hay proxy, usa request.client.host
    return request.client.host if request.client else "unknown"