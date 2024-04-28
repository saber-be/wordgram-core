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
    update_all_posts: Optional[bool] = False
    force_update: Optional[bool] = False
    sync_instagram: Optional[bool] = True
    params: Optional[dict] = None
    instagram_user_id: Optional[str] = None

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
                "update_images": True,
                "update_all_posts": False,
                "force_update": False,
                "sync_instagram": True,
            }
        }
