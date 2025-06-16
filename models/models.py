from pydantic import BaseModel


class logModel(BaseModel):
    req_type: str
    path: str
    req_body: str
    process_time: float