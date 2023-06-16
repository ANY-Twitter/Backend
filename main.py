from fastapi import FastAPI, Response,Form, UploadFile,File,HTTPException
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
    hallar = usuario.find_one({'handle': usr.handle})

    hasher = SHA256.new()
    hasher.update(usr.password.encode() + hallar['salt']) 
    usr.password = hasher.digest()

    if not hallar or hallar['hashed_pass'] != usr.password:
        rpta.status_code = 400
        return "El correo o clave es incorrecto"

    return {'name':hallar['name'], 'handle': hallar['handle'], 'srcProfilePicture': ''} 

@anytwitter.post("/crearUsuario", status_code=200)
async def registrar(name: Annotated[str,Form()],
                    handle: Annotated[str,Form()], 
                    password: Annotated[str,Form()], 
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
                        'pictureName': pictureName})
    

    return {'name':name, 'handle': handle, 'srcProfilePicture': srcProfilePicture} 