from mongo.mongoManager import mongoEventManger


class eventManager:
    def __init__(self):
        self.mongoEventer = mongoEventManger()

    def track_event(self, event, coleccion):
        return self.mongoEventer.insert_event(event, coleccion)
