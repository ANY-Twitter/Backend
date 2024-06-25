
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

def conexion_mongo(uri: str) -> MongoClient:
    cliente = MongoClient(uri)
    # cliente = MongoClient(uri, server_api=ServerApi('1'))    
    try:
        cliente.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)    
    return cliente