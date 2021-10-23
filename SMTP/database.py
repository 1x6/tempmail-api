from pymongo import MongoClient

connection = MongoClient("mongodb srv connection url")
db = connection.get_database("tempmail").get_collection("emails")
