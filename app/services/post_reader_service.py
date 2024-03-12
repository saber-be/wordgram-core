import re

class PostReaderService:
    @staticmethod
    def instaToWordGramMapper(instaPost):
        print(instaPost)
        caption = instaPost["caption_text"].split("\n")
        name = caption[0][:50]
        description = instaPost["caption_text"]
        
        if len(caption) > 1:
            description = "\n".join(caption[1:])

        tags, clean_description = PostReaderService.getTagsAndCaption(description)
        wordGramPost = {
            "Name": name,
            "Description": clean_description,
            "SKU": instaPost["code"],
            "Price": PostReaderService.getPrice(description),
            "QTY": 100,
            "tags": PostReaderService.getPostTags(tags),
            "Images": []
        }
        thumbnail = instaPost["thumbnail_url"]
        if(thumbnail):
            wordGramPost["Images"].append({"url": thumbnail})

        images = instaPost["resources"]
        for image in images:
            wordGramPost["Images"].append({"url": image["thumbnail_url"]})

        return wordGramPost



    @staticmethod
    def getPrice(caption):
        # example : قیمت💰: 448 تومان 
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
