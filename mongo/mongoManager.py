from pymongo import MongoClient
from nanoid import generate
from models.models import logModel
import os

class mongoAuthManager:
    
    def __init__(self):
        client = MongoClient(f"mongodb://{os.getenv('MONGO_URL')}/")
        
        db = client["service"]
        self.coleccionAuth = db["apikeys"]

    def get_api_key(self, api_key: str):
        result = self.coleccionAuth.find_one({"api_key": api_key})
        print(result)
        return result
    
    def insert_api_key(self, api_key: str, tier: str):
        col_id = generate(size=10)
        entrada = { "api_key": api_key, "tier":tier, "col_id": col_id }
        self.coleccionAuth.insert_one(entrada)
        return api_key



class mongoLogManager:
    
    def __init__(self):
        client = MongoClient(f"mongodb://{os.getenv('MONGO_URL')}/")
        
        db = client["service"]
        self.coleccionAuth = db["logs"]
    
    def insert_entry(self, log: logModel):
        entrada = { "req_type": log.req_type, "path": log.path, "req_body": log.req_body, "process_time": log.process_time }
        self.coleccionAuth.insert_one(entrada)
        return "OK"



class mongoEventManger:
    def __init__(self):
        client = MongoClient(f"mongodb://{os.getenv('MONGO_URL')}/")
        
        self.db = client["events"]

    def insert_event(self, eventdic, col_id):
        event = eventdic
        coleccion = self.db[col_id]
        coleccion.insert_one(event)
        return "OK"