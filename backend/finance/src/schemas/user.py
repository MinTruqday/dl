from pydantic import BaseModel, Field

class UserInDB(BaseModel):
    id: str = Field(alias="_id")
