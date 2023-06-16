from pydantic import BaseModel

class Usuario(BaseModel):
    name: str
    handle: str
    password: str
    # salt: str
    # rclave: str | None=None
