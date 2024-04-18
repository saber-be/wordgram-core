from typing import Optional
from pydantic import BaseModel


class updateWebSiteRequest(BaseModel):
    instagram_username: str
    SUK: Optional[str] = None
    api_key: str
    state: str
    update_price: Optional[bool] = True
    update_title: Optional[bool] = True
    update_quality: Optional[bool] = True
    update_description: Optional[bool] = True
    update_tags: Optional[bool] = True
    update_images: Optional[bool] = True
    force_update: Optional[bool] = False
    params: Optional[dict] = None

    class Config:
        schema_extra = {
            "example": {
                "instagram_username": "my_shop",
                "SUK": "123456",
                "api_key": "1ds2fev6r5gv",
                "state": "16513206",
                "update_price": True,
                "update_title": True,
                "update_quality": True,
                "update_description": True,
                "update_tags": True,
                "force_update": False,
                "params": {"key": "value"},
            }
        }
