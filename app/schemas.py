from pydantic import BaseModel, EmailStr
import models

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

class RegisterResponse(BaseModel):
    user_info: UserPublic  # This key will contain a UserPublic object
    token: Token


# for getTest()
class OptionPublic(BaseModel):
    option_id: str
    option_text: str
    image_url: str | None = None

    class Config:
        from_attributes = True

# A schema for a single question, using the public Option schema.
class QuestionPublic(BaseModel):
    question_id: str
    question_text: str
    image_url: str | None = None
    question_type: models.QuestionTypeEnum # You can import this from models
    positive_marks: int
    negative_marks: int
    options: list[OptionPublic] = []

    class Config:
        from_attributes = True

# The main response model for the getTest() endpoint.
class TestDetail(BaseModel):
    template_id: str
    template_name: str
    description: str | None = None
    duration_minutes: int
    test_type: models.TestTypeEnum
    questions: list[QuestionPublic] = []

    class Config:
        from_attributes = True