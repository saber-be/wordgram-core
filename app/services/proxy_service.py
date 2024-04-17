import requests
import os
import urllib.parse
from fastapi.responses import StreamingResponse
class ProxyService:
    @staticmethod
    def get_bypass_url(url: str) -> str:
        
        encoded_url = urllib.parse.quote(url)
        return  os.environ.get('BASE_URL') + "/proxy/?url=" + encoded_url
        
    @staticmethod
    def fetch_image(image_url) -> bytes:
        decoded_url = urllib.parse.unquote(image_url)
        response = requests.get(decoded_url, stream=True)
        response.raise_for_status()  # Check if the request was successful

        # Set the appropriate content type
        content_type = response.headers.get("content-type", "image/jpeg")

        # Stream the image content to the user's browser
        return StreamingResponse(response.iter_content(chunk_size=1024), media_type=content_type)