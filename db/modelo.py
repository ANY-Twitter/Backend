from pydantic import BaseModel

class Usuario(BaseModel):
    name: str | None = None
    handle: str
    password: str
    # salt: str
    # rclave: str | None=None

class Tweet(BaseModel):
    handle: str
    data: str

class InfoUsuario(BaseModel):
    handle: str
    name: str
    pictureName: str

class TweetWithInfo(BaseModel):
    data: str
    usuario: list[InfoUsuario]
    id: str
