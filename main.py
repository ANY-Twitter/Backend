from fastapi import FastAPI, Response,Form, UploadFile,File
from Crypto import Random
from Crypto.Hash import SHA256
import aiofiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import dotenv_values
from typing import Annotated,Optional
from db.cliente import conexion_mongo
from db.modelo import Usuario
config = dotenv_values(".env")

# cliente = conexion_mongo(config['URI_MONGO_CLOUD'])
cliente = conexion_mongo(config['MONGO_URI'])
db = cliente['anytwitter']
usuario = db['usuario']


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
    hallar = usuario.find_one({'correo': usr.correo})
    if not hallar or hallar['clave'] != usr.clave:
        rpta.status_code = 400
        return "El correo o clave es incorrecto"

    return "Iniciado sesion exitosamente"

@anytwitter.post("/crearUsuario", status_code=200)
async def registrar(name: Annotated[str,Form()],
                    handle: Annotated[str,Form()], 
                    password: Annotated[str,Form()], 
                    rpta: Response,
                    user_photo: Optional[Annotated[UploadFile,File]] = File(None)):
    hallar = usuario.find_one({'handle': handle})
    if hallar:
        rpta.status_code = 400
        return "El correo ya fue registrado"
    salt_size = 16

    random_gen = Random.new()
    hasher = SHA256.new()
    salt = random_gen.read(salt_size)
    print(salt)
    # print(len(password.encode()))
    # print(len(password.encode() + salt))
    # print(user_photo)
    hasher.update(password.encode() + salt) 
    hashed_pass = hasher.digest()

    if user_photo:
        base_dir = './images/'
        async with aiofiles.open(base_dir + user_photo.filename,'wb') as out_file:
            content = await user_photo.read()
            await out_file.write(content)
        
    usuario.insert_one({'name':name,
                        'handle':handle,
                        'hashed_pass':hashed_pass,
                        'salt':salt})
    return "Usuario creado exitosamente"