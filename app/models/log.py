from pydantic import BaseModel
from datetime import datetime

class Log(BaseModel):
    message: str
    level: str
    timestamp: datetime = datetime.now()