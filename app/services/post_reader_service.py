import re
import os
from app.models.updateWebSiteRequest import updateWebSiteRequest
from app.services.proxy_service import ProxyService

class PostReaderService:
    @staticmethod
    def instaToWordGramMapper(instaPost, update_request: updateWebSiteRequest):
        print(instaPost)
        base_url = os.getenv("BASE_URL")
        wordGramPost = {}
        if "code" in instaPost:
            wordGramPost["SKU"] = instaPost["code"]
        caption = instaPost["caption_text"].split("\n")
        name = caption[0][:50]
        description = instaPost["caption_text"]

        if len(caption) > 1:
            description = "\n".join(caption[1:])
        clean_description = ''
        tags = []
        if update_request.update_description or update_request.update_tags:
            tags, clean_description = PostReaderService.getTagsAndCaption(
                description)

        if update_request.update_description:
            wordGramPost["Description"] = clean_description

        if update_request.update_tags:
            wordGramPost["tags"] = PostReaderService.getPostTags(tags)

        if update_request.update_price:
            wordGramPost["Price"] = PostReaderService.getPrice(description)

        if update_request.update_title:
            wordGramPost["Name"] = name

        if update_request.update_quality:
            wordGramPost["QTY"] = 100

        if update_request.update_images:
            wordGramPost["Images"] = []
            thumbnail = instaPost["thumbnail_url"]
            if (thumbnail):
                image_url = ProxyService.get_bypass_url(thumbnail) if "https" in base_url else thumbnail
                wordGramPost["Images"].append({"url": image_url})

            images = instaPost["resources"]
            for image in images:
                image_url = ProxyService.get_bypass_url(image["thumbnail_url"]) if "https" in base_url else image["thumbnail_url"]
                wordGramPost["Images"].append({"url": image_url})

        return wordGramPost

    @staticmethod
    def getPrice(caption):
        # Regular expression pattern to match price values
        price_pattern = r"قیمت\D*([\d,.]+)"
        # Search for the price pattern in the caption
        match = re.search(price_pattern, caption)
        if match:
            # Extract the matched price
            price_str = match.group(1)
            # Remove any non-digit characters except dot and comma
            price_str = re.sub(r"[^\d,.]", "", price_str)
            # Convert comma to dot for decimal points
            price_str = price_str.replace(",", ".")
            # Convert the price string to float
            price = float(price_str)
            # Multiply by 1000 if the price is less than 1000
            if price < 1000:
                price *= 1000
                return price
            else:
                return None

    @staticmethod
    def getTagsAndCaption(caption):
        # example : #tag1 #tag2
        # output : ["tag1", "tag2"]
        clean_caption = caption
        tags = []
        if "#" in caption:
            caption = caption.replace(",", " ")
            caption = caption.replace("#", " #")
            caption_tags = caption.split(" ")
            tags = [tag[1:] for tag in caption_tags if tag.startswith("#")]
        # remove tags from clean_caption
        for tag in tags:
            clean_caption = re.sub(rf"#{tag}\b", "", clean_caption)
        return tags, clean_caption

    @staticmethod
    def getPostTags(tags):
        # example : ["tag1", "tag2"]
        # output : [{"name": "tag1"}, {"name": "tag2"}]
        postTags = []
        for tag in tags:
            postTags.append({"name": tag})
        return postTags
