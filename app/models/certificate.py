from typing import Optional
from pydantic import BaseModel, HttpUrl


class Certificate(BaseModel):
    instagram_username: str
    api_key: str
    state: str
    platform: str
    params: Optional[dict] = None

    class Config:
        schema_extra = {
            "example": {
                "instagram_username": "my_shop",
                "api_key": "1ds2fev6r5gv",
                "state": "16513206",
                "platform": "E-commerce",
                "params": {"key": "value"},
            }
        }
