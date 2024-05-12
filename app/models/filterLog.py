from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
class FilterLog(BaseModel):
    message: Optional[str]
    level: Optional[str]
    service: Optional[str]
    start_timestamp: datetime = datetime.now() - timedelta(days=1)
    end_timestamp: datetime = datetime.now()
    per_page: int = 40
    page: int = 1
    sort_by: str = "timestamp"
    sort_direction: str = "desc"
    class Config:
        schema_extra = {
            "example": {
                "message": "",
                "level": "ERROR",
                "service": "",
                "start_timestamp": "2024-01-01T00:00:00.000Z",
                "end_timestamp": "2024-01-02T00:00:00.000Z",
                "per_page": 40,
                "page": 1,
                "sort_by": "timestamp",
                "sort_direction": "desc"
            }
        }