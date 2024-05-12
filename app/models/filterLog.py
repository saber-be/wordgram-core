from typing import Optional
from pydantic import BaseModel
from datetime import datetime
class FilterLog(BaseModel):
    message: Optional[str]
    level: Optional[str]
    service: Optional[str]
    start_timestamp: datetime = datetime.now()
    end_timestamp: datetime = datetime.now()
    per_page: int = 40
    page: int = 1
    sort_by: str = "timestamp"
    sort_direction: str = "desc"