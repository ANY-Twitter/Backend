from fastapi import FastAPI, Response
from dotenv import dotenv_values
from db.cliente import conexion_mongo
from db.modelo import Usuario
config = dotenv_values(".env")

cliente = conexion_mongo(config['CLAVE_MONGO'])
db = cliente['anytwitter']
usuario = db['usuario']


anytwitter = FastAPI()


@anytwitter.get("/")
async def root():
    return {"message": "Hello World"}

@anytwitter.post("/usuarios")
async def iniciar_sesion(usr: Usuario, rpta: Response):
    hallar = usuario.find_one({'correo': usr.correo})
    if not hallar or hallar['clave'] != usr.clave:
        rpta.status_code = 400
        return "El correo o clave no ha sido registrado"
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