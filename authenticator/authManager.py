from mongo.mongoManager import mongoAuthManager
import uuid


class authManager:
    def __init__(self):
        self.mongoAuth = mongoAuthManager()

    def validate_key(self, apikey):
        data = self.mongoAuth.get_api_key(apikey)
        if(data):
            if(data['tier'] == 'premium'):
                return "premium"
            elif(data['tier'] == 'freemium'):
                return "freemium"
            else:
                return "invalid"
        
        return "invalid"
        
    def generate_key(self, tier):
        if (tier == 'freemium' or tier == 'premium'):
            api_key = str(uuid.uuid4())
            return self.mongoAuth.insert_api_key(api_key, tier)
        else:
            return

    def get_coleccion(self, api_key):
        data = self.mongoAuth.get_api_key(api_key)
        return data['col_id']

