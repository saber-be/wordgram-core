import re
from app.models.updateWebSiteRequest import updateWebSiteRequest


class PostReaderService:
    @staticmethod
    def instaToWordGramMapper(instaPost, update_request: updateWebSiteRequest):
        print(instaPost)
        wordGramPost = {}
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
                wordGramPost["Images"].append({"url": thumbnail})

            images = instaPost["resources"]
            for image in images:
                wordGramPost["Images"].append({"url": image["thumbnail_url"]})

        return wordGramPost

    @staticmethod
    def getPrice(caption):
        # example : قیمت💰: 448 توما 
        # output : 448
        price = 0
        caption = caption.split("\n")
        for line in caption:
            if "قیمت" in line:
                price = line
                price = ''.join(filter(str.isdigit, price))
                if price.isdigit():
                    price = int(price) * 1000
                    break
        return price

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
