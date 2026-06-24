from pydantic import BaseModel

class Registration(BaseModel):
    document_id: str
    user_id: str

class Confirmation(BaseModel):
    file_id: str
    aes_key: str

class Acquisition(BaseModel):
    file_id: str

class Token(BaseModel):
    aes_key: str
