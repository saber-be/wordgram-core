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
                "instagram_username": "Moonlandir",
                "SUK": "123456",
                "api_key": "8240f2baf3884fae0972d2cdac3051ea",
                "state": "1520066218a441744b",
                "update_price": True,
                "update_title": True,
                "update_quality": True,
                "update_description": True,
                "update_tags": True,
                "force_update": False,
                "params": {"key": "value"},
            }
        }
