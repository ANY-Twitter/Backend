from pydantic import BaseModel
from datetime import datetime

class Usuario(BaseModel):
    name: str | None = None
    handle: str
    password: str
    # salt: str
    # rclave: str | None=None

class Tweet(BaseModel):
    handle: str
    data: str
    date: datetime

class InfoUsuario(BaseModel):
    handle: str
    name: str
    pictureName: str

class UserKeys(BaseModel):
    handle: str
    keys: str
    name: str



class TweetWithInfo(BaseModel):
    data: str
    usuario: list[InfoUsuario]
    id: str
    date: datetime

class MessageWithInfo(BaseModel):
    id: str
    message: str
    signedHash: str

class Message(BaseModel):
    message: str
    signedHash: str