from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import dotenv_values
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
async def registrar(usr: Usuario, rpta: Response):
    hallar = usuario.find_one({'correo': usr.correo})
    if hallar:
        rpta.status_code = 400
        return "El correo ya fue registrado"
    if usr.clave != usr.rclave:
        rpta.status_code = 400
        return "Las contraseñas no coinciden" 
    usuario.insert_one(usr.dict())
    return "Usuario creado exitosamente"