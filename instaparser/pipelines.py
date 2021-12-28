# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import scrapy
from itemadapter import ItemAdapter
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from scrapy.pipelines.images import ImagesPipeline


class InstaparserPipeline:
    def __init__(self):
        client = MongoClient('localhost', 27017)
        self.db = client.db_instagram_friends

    def process_item(self, item, spider):
        collection = self.db[item['friend']]
        try:
            collection.update_one(item)
        except DuplicateKeyError as e:
            print(e, item['user_id'])
        return item


class InstaparserImagesPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        if item['photo']:
            try:
                yield scrapy.Request(item['photo'])
            except Exception as e:
                print(e)

    def file_path(self, request, response=None, info=None, *, item=None):
        return f'{item["friend"]}/{item["follow"]}/{item["user_id"]}.jpg'
