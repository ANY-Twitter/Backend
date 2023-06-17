from fastapi import FastAPI, Response,Form, UploadFile,File,HTTPException
import json
from Crypto import Random
from Crypto.Hash import SHA256
import aiofiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import dotenv_values
from typing import Annotated,Optional
from db.cliente import conexion_mongo
from db.modelo import Usuario
from bson import ObjectId
config = dotenv_values(".env")

# cliente = conexion_mongo(config['URI_MONGO_CLOUD'])
cliente = conexion_mongo(config['MONGO_URI'])
db = cliente['anytwitter']
usuario = db['usuario']
mensajes = db['mensajes']


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

@anytwitter.get("/getKeys/{handle}")
async def get_keys(handle: str,response: Response):

    print(handle)
    user = usuario.find_one({'handle': handle})

    if not user: 
        response.status_code = 400
        return "Usuario no encontrado"
    
    print(user)
    return json.loads(user['public_keys'])


@anytwitter.post("/submitMessage")
async def submit_message(message: Annotated[UploadFile,File()],
                         hash_: Annotated[UploadFile,File()],
                         signedHash: Annotated[UploadFile,File()]):
    
   
    messageBytes = await message.read()
    hashBytes = await  hash_.read()
    signedHashBytes = await signedHash.read()

    print(len(messageBytes))
    print(len(hashBytes))
    print(len(signedHashBytes))

    mensajes.insert_one({'message': messageBytes, 'hash': hashBytes, 'signedHash': signedHashBytes})

    return "uwu"

@anytwitter.get("/obtenerMensajes")
async def obtener_mensajes():
    retorno = mensajes.find()


    retorno = list(retorno)
    for i in range(len(retorno)):
        # retorno[i].pop('_id')
        retorno[i]['_id'] = str(retorno[i]['_id'])
        retorno[i]['hash'] = retorno[i]['hash'].hex()
        retorno[i]['message'] = retorno[i]['message'].hex()
        retorno[i]['signedHash'] = retorno[i]['signedHash'].hex()

    # print(retorno['hash'])
    return retorno

""" @anytwitter.get("/obtenerMensajes")
async def obtener_mensajes():
    retorno = mensajes.find()
    return [str(d['_id']) for d in retorno]


    retorno = list(retorno)
    for i in range(len(retorno)):
        retorno[i].pop('_id')
    print(retorno[0]['hash'])        
    return Response(content=retorno[0]['hash'], media_type="application/octet-stream")
    # print(retorno['hash'])
    # return  """

@anytwitter.get("/obtenerCampo")
async def obtener_campo(_id:str, campo: str):
    retorno = mensajes.find_one({'_id': ObjectId(_id)})
    return Response(content=retorno[campo], media_type="application/octet-stream")

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
        pictureName = hashed_name + extension

        dstProfilePicture = base_dir + '.' + pictureName 
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