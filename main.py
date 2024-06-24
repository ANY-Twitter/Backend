from fastapi import FastAPI, Response,Form, UploadFile,File,HTTPException
from fastapi.responses import StreamingResponse
import json
from Crypto import Random
from Crypto.Hash import SHA256
import aiofiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated,Optional
from db.cliente import conexion_mongo
from db.modelo import Usuario, Tweet, TweetWithInfo, Message, MessageWithInfo, UserKeys
from bson import ObjectId

# cliente = conexion_mongo(config['URI_MONGO_CLOUD'])
cliente = conexion_mongo(config['MONGO_URI'])
db = cliente['anytwitter']
usuario = db['usuario']
mensajes = db['mensajes']
tweets = db['tweets']


anytwitter = FastAPI()


origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:5173",
]

anytwitter.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@anytwitter.get("/")
async def root():
    return {"message": "Hello World"}

@anytwitter.post("/usuarios")
async def iniciar_sesion(usr: Usuario, rpta: Response):
    hallar = usuario.find_one({'handle': usr.handle})
    if not hallar:
        rpta.status_code = 400
        return "El usuario no existe"

    hasher = SHA256.new()
    hasher.update(usr.password.encode() + hallar['salt']) 
    usr.password = hasher.digest()

    if hallar['hashed_pass'] != usr.password:
        rpta.status_code = 400
        return "El correo o clave es incorrecto"

    return {'name':hallar['name'], 'handle': hallar['handle'], 'srcProfilePicture': ''} 


@anytwitter.get("/getKeysList",response_model=list[UserKeys])
async def get_user_list():
    user_keys = usuario.aggregate([{"$project":{'_id':0,'handle':1,'name':1,'keys':'$public_keys'}}])

    return list(user_keys) 


@anytwitter.get("/getKeys/{handle}")
async def get_keys(handle: str,response: Response):

    print(handle)
    user = usuario.find_one({'handle': handle})

    if not user: 
        response.status_code = 400
        return "Usuario no encontrado"
    
    print(user)
    return json.loads(user['public_keys'])


@anytwitter.post("/tweet")
async def tweet(tweet_data: Tweet, response: Response):

    print(tweet_data.date.isoformat())

    user = usuario.find_one({'handle':tweet_data.handle})

    if not user: 
        response.status_code = 400
        return "Usuario no encontrado"
    
    tweets.insert_one({'handle':tweet_data.handle,'data': tweet_data.data,'date':tweet_data.date})

 
    return "Inicio exitoso"

@anytwitter.post("/submitMessage")
async def submit_message(message: Message):
    
   
    print(len(message.message))
    print(len(message.signedHash))

    mensajes.insert_one({'message': message.message, 'signedHash': message.signedHash})

    return "successful submit"

@anytwitter.get("/obtenerMensajes",response_model=list[MessageWithInfo])
async def obtener_mensajes():

    retorno = mensajes.aggregate([{"$project":
                        {"id":{"$toString":"$_id"},
                         "_id":0,
                         "message":1,
                         "signedHash":1}
                       }])
    retorno = list(retorno)
    return retorno

@anytwitter.get("/obtenerTweets",response_model=list[TweetWithInfo])
async def obtener_tweets():
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
    #db.tweets.aggregate([{ "$lookup": { "from": "usuario", "localField": "handle", "foreignField": "handle", "as": "usuario" } }, {"$sort": {"date":-1}}, { "$project": { "id": {'$toString': "$_id"}, "data": 1, "usuario": {"$first" : "$usuario"} , "date":1, "_id":0 } },{"$unset": ["usuario.hashed_pass","usuario.public_keys","usuario._id","usuario.salt"]}])
    all_tweets = list(all_tweets)


    
    return all_tweets 




@anytwitter.post("/crearUsuario", status_code=200)
async def registrar(name: Annotated[str,Form()],
                    handle: Annotated[str,Form()], 
                    password: Annotated[str,Form()], 
                    keys: Annotated[str,Form()],
                    rpta: Response,
                    user_photo: Optional[Annotated[UploadFile,File]] = File(None)):
    hallar = usuario.find_one({'handle': handle})
    if hallar:
        rpta.status_code = 400
        return "El usuario ya fue registrado"
    salt_size = 16

    random_gen = Random.new()
    hasher = SHA256.new()
    salt = random_gen.read(salt_size)
    # print(salt)
    # print(len(password.encode()))
    # print(len(password.encode() + salt))
    # print(user_photo)
    hasher.update(password.encode() + salt) 
    hashed_pass = hasher.digest()

    pictureName = ''
    srcProfilePicture = ''

    if user_photo:
        base_dir = './images/'
        content_type = user_photo.content_type
        if content_type not in ["image/jpeg", "image/png", "image/gif"]:
            rpta.status_code = 400
            # raise HTTPException(status_code=400, detail="Invalid file type")
            return "Formato invalido"
        
        extension = content_type.split('/')[1]

        hasher.update((user_photo.filename + handle).encode())
        hashed_name = hasher.hexdigest()
        print(hashed_name)
        pictureName = hashed_name + '.' +  extension

        dstProfilePicture = base_dir + pictureName 
        # pictureName = user_photo.filename



        srcProfilePicture = 'http://127.0.0.1:8000/images/' + pictureName
        async with aiofiles.open(dstProfilePicture,'wb') as out_file:
            content = await user_photo.read()
            await out_file.write(content)
        
        
    usuario.insert_one({'name':name,
                        'handle':handle,
                        'hashed_pass':hashed_pass,
                        'salt':salt,
                        'public_keys': keys,
                        'pictureName': pictureName})
    

    return {'name':name, 'handle': handle, 'srcProfilePicture': srcProfilePicture} 