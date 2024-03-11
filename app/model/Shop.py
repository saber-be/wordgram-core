import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl


class Shop(BaseModel):
    shop_name: str
    platform: str
    platform_url: str
    redirect_url: str
    product_webhook_url: str
    order_webhook_url: str
    instagram_username: str
    params: Optional[dict] = None
    created_at: Optional[datetime.datetime] = None
    class Config:
        schema_extra = {
            "example": {
                "shop_name": "My Shop",
                "platform": "E-commerce",
                "platform_url": "https://example.com",
                "redirect_url": "https://example.com/redirect",
                "product_webhook_url": "https://example.com/webhook/product",
                "order_webhook_url": "https://example.com/webhook/order",
                "instagram_username": "my_shop",
                "params": {"key": "value"},
                "created_at": "2022-01-01T00:00:00.000Z"
            }
        }