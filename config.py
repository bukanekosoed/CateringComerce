from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    MONGO_URI = os.getenv('MONGO_URI')
    DB_NAME = os.getenv('DB_NAME')
    SESSION_TYPE = os.getenv('SESSION_TYPE')
    MIDTRANS_SERVER_KEY = os.getenv('MIDTRANS_SERVER_KEY')
    MIDTRANS_CLIENT_KEY = os.getenv('MIDTRANS_CLIENT_KEY')
    SESSION_MONGODB_DB = os.getenv('SESSION_MONGODB_DB')
    SESSION_MONGODB_COLLECT = os.getenv('SESSION_MONGODB_COLLECT')
    SESSION_MONGODB = MONGO_URI
