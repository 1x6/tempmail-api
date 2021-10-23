from pydantic import BaseModel

class create(BaseModel):
    username: str
    password: str
    domain: str

class latest(BaseModel):
    address: str
    password: str
    from_address: str = None
