import azure.functions as func
import logging
from db.schemas import Usuario, UsuarioSchema, Tweet, Message
from json import dumps
from Crypto.Hash import SHA256
from Crypto import Random
from db.cliente import conexion_mongo
from os import getenv, path
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from urllib.parse import quote_plus

app = func.FunctionApp()

connect_str = getenv('AZURE_STORAGE_CONNECTION_STRING')
blob_service_client = BlobServiceClient.from_connection_string(connect_str)
container_name = "anytwitter"

cliente = conexion_mongo(f"mongodb://{quote_plus(getenv('MONGO_USERNAME'))}:{quote_plus(getenv('MONGO_PASSWORD'))}@anytwitter.mongo.cosmos.azure.com:10255/?ssl=true&retrywrites=false&maxIdleTimeMS=120000&appName=@anytwitter@")

db = cliente['anytwitter']
usuario = db['usuario']
mensajes = db['mensajes']
tweets = db['tweets']

@app.route(route='base', methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def index(req: func.HttpRequest) -> func.HttpResponse:

    return func.HttpResponse("Hello, world")

@app.route(route="login", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def iniciar_sesion(req: func.HttpRequest) -> func.HttpResponse:

    usr = UsuarioSchema().load(req.get_json())

    hallar = usuario.find_one({'handle': usr.handle})
    if not hallar:
        return func.HttpResponse("El usuario no existe", status_code=400)

    hasher = SHA256.new()
    hasher.update(usr.password.encode() + hallar['salt']) 
    usr.password = hasher.digest()

    if hallar['hashed_pass'] != usr.password:
        return func.HttpResponse("El correo o clave es incorrecto", status_code=400)

    return func.HttpResponse(dumps({'name':hallar['name'], 'handle': hallar['handle'], 'srcProfilePicture': ''}), mimetype="application/json")

@app.route(route="getKeysList", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_user_list(req: func.HttpRequest) -> func.HttpResponse:
    user_keys = usuario.aggregate([{"$project":{'_id':0,'handle':1,'name':1,'keys':'$public_keys'}}])

    return func.HttpResponse(dumps(list(user_keys)), mimetype="application/json")

@app.route(route="getKeys/{handle}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_keys(req: func.HttpRequest) -> func.HttpResponse:
    
    handle = req.route_params.get('handle')
    print(handle)
    user = usuario.find_one({'handle': handle})

    if not user:
        return func.HttpResponse("Usuario no encontrado", status_code=400)
    
    print(user)
    return func.HttpResponse(dumps(user['public_keys']), mimetype="application/json")

@app.route(route="tweet", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def tweet(req: func.HttpRequest) -> func.HttpResponse:
    tweet_data = Tweet().load(req.get_json())

    print(tweet_data.date.isoformat())

    user = usuario.find_one({'handle':tweet_data.handle})

    if not user: 
        return func.HttpResponse("Usuario no encontrado", status_code=400)
    
    tweets.insert_one({'handle':tweet_data.handle,'data': tweet_data.data,'date':tweet_data.date})

    return func.HttpResponse("Inicio exitoso", status_code=200)

@app.route(route="submitMessage", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def submit_message(req: func.HttpRequest) -> func.HttpResponse:

    message = Message().load(req.get_json())

    print(len(message.message))
    print(len(message.signedHash))

    mensajes.insert_one({'message': message.message, 'signedHash': message.signedHash})

    return func.HttpResponse("Mensaje subido", status_code=200)

@app.route(route="obtenerMensajes", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def obtener_mensajes(req: func.HttpRequest) -> func.HttpResponse:
    
        retorno = mensajes.aggregate([{"$project":
                            {"id":{"$toString":"$_id"},
                            "_id":0,
                            "message":1,
                            "signedHash":1}
                        }])
        retorno = list(retorno)
        return func.HttpResponse(dumps(retorno), mimetype="application/json")

@app.route(route="obtenerTweets", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def obtener_tweets(req: func.HttpRequest) -> func.HttpResponse:
    all_tweets = tweets.aggregate([#{"$match": {"handle": '2'}}, 
                         { "$lookup": { 
                             "from": "usuario", 
                             "localField": "handle", 
                             "foreignField": "handle", 
                             "as": "usuario" } 
                             }, 
                         {"$sort": {"date":-1}},
                         { "$project": { 
                             "id": {'$toString': "$_id"},
                             "data": 1, 
                             "usuario.name": 1, 
                             "usuario.handle": 1, 
                             "usuario.pictureName": 1,
                             "date":1,
                             "_id":0
                             } 
                         }])
    all_tweets = list(all_tweets)
    
    return func.HttpResponse(dumps(all_tweets), mimetype="application/json")

@app.route(route="crearUsuario", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def registrar(req: func.HttpRequest) -> func.HttpResponse:

    name = req.form.get('name')
    handle = req.form.get('handle')
    password = req.form.get('password')
    keys = req.form.get('keys')

    print(req.form)

    user_photo = req.files.get('user_photo')

    hallar = usuario.find_one({'handle': handle})
    if hallar:
        return func.HttpResponse("El usuario ya fue registrado", status_code=400)
    salt_size = 16

    random_gen = Random.new()
    hasher = SHA256.new()
    salt = random_gen.read(salt_size)

    hasher.update(password.encode() + salt)
    hashed_pass = hasher.digest()

    pictureName = ''
    srcProfilePicture = ''

    if user_photo:
        content_type = user_photo.content_type

        if content_type not in ["image/jpeg", "image/png", "image/gif"]:
            return func.HttpResponse("Formato invalido", status_code=400)
        
        extension = content_type.split('/')[1]


        hasher.update((user_photo.filename + handle).encode())
        hashed_name = hasher.hexdigest()
        print(hashed_name)
        pictureName = hashed_name + '.' +  extension

        srcProfilePicture += f"{getenv('IMAGES_ENDPOINT')}/images/{pictureName}"

        blob_path = path.join("images",pictureName)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_path)
        blob_client.upload_blob(user_photo.stream.read(), content_type=content_type)
            

    usuario.insert_one({'name':name
                        ,'handle':handle
                        ,'hashed_pass':hashed_pass
                        ,'salt':salt
                        ,'public_keys': keys
                        ,'pictureName': pictureName})
    
    return func.HttpResponse(dumps({'name':name, 'handle': handle, 'srcProfilePicture': srcProfilePicture}), mimetype="application/json")

