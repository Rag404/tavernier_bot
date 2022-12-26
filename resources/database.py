from data.config import DB_NAME
from pymongo import MongoClient
from dotenv import load_dotenv
from os import getenv

# Private .env file
load_dotenv()
db_link = getenv("DATABASE")

# MongoDB Atlas connection
db_client = MongoClient(db_link)
database = db_client.get_database(DB_NAME)