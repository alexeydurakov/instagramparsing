
from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client.db_instagram_friends

collection = db['sweet_cakes_tortberry']

cursor = collection.find({'username': "alexeydurakov"})

print(cursor)