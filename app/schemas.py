from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserPublic(BaseModel):
    user_id: str
    email: EmailStr
    name: str

    class Config:
        from_attributes = True 

# Schema for the JWT token response
class Token(BaseModel):
    access_token: str
    token_type: str

# Schema for the data embedded within the JWT
class TokenData(BaseModel):
    email: str | None = None