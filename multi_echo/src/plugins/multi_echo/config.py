from pydantic import BaseModel


class EchoConfig(BaseModel):
    superuser: int
