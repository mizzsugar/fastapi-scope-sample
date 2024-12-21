from pydantic import BaseModel


class UserInDB(BaseModel):
    id: int
    username: str
    scopes: list[str]

    class Config:
        from_attributes = True
