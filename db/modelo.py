from pydantic import BaseModel

class Usuario(BaseModel):
    correo: str
    clave: str
    rclave: str | None=None
