
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

def conexion_mongo(uri: str) -> MongoClient:
    # uri = f"mongodb+srv://grovereiner:{clave}@anytwitter.jkwv4zi.mongodb.net/?retryWrites=true&w=majority"
    cliente = MongoClient(uri, server_api=ServerApi('1'))    
    try:
        cliente.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)    
    return cliente