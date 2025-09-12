from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import uuid
from sqlalchemy import select

# project modules
from . import models, schemas
from .database import engine, get_db
from .config import settings


from fastapi.middleware.cors import CORSMiddleware

# Use alembic

# --- Security & Hashing Setup ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI()

# --- CORS ---
# 2. DEFINE THE ALLOWED ORIGINS (FRONTEND ADDRESSES)
# For development, we can be permissive. Flutter web uses random ports.
# We include the standard localhost addresses.
origins = ["*"]
    #"http://localhost",
    #"http://localhost:8080",
    # Add any other specific port your Flutter app runs on if you know it
    # Or for maximum ease in local dev, you could use "*"
    # "http://localhost:54321" # Example of a specific Flutter dev port
#]


# 3. ADD THE MIDDLEWARE TO YOUR APP
# This should be added before your routes are defined.
app.add_middleware(
    CORSMiddleware,
    #allow_origins=origins, # Allows specific origins
    allow_origins=["*"], # Or, allow all origins
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)


# --- Utility Functions ---

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# --- Endpoints ---

@app.post("/register", response_model=schemas.UserPublic)
async def register_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user with that email already exists
    # Note: A proper implementation would have a dedicated function for this query
    existing_user = await db.execute(select(models.User).where(models.User.email == user.email))
    if existing_user.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    hashed_password = get_password_hash(user.password)
    new_user = models.User(
        user_id=str(uuid.uuid4()), 
        email=user.email, 
        name=user.name, 
        password_hash=hashed_password
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user

@app.post("/login", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    # Note: form_data will have 'username' and 'password' fields.
    # We use the 'username' field for the email.
    user_result = await db.execute(select(models.User).where(models.User.email == form_data.username))
    user = user_result.scalars().first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/getTest")
async def sendTest():
    return {
        "sessionId": "session_mock_12345",
        "testId": "jee_main_mock_01",
        "testName": "Mock Test for Development",
        "durationInSeconds": 3600, # 1 hour
        "sections": [
            {
                "sectionId": "phy_sec_1",
                "sectionName": "Physics Sec 1",
                "questions": [
                    {
                        "questionId": "q_phy_01",
                        "questionText": "What is the unit of force?",
                        "questionImageUrl": None,
                        "type": "MCQ",
                        "positiveMarks": 4,
                        "negativeMarks": -1,
                        "options": [
                            {"optionId": "opt_p1_a", "optionText": "Newton", "optionImageUrl": None},
                            {"optionId": "opt_p1_b", "optionText": "Watt", "optionImageUrl": None},
                            {"optionId": "opt_p1_c", "optionText": "Joule", "optionImageUrl": None},
                            {"optionId": "opt_p1_d", "optionText": "Pascal", "optionImageUrl": None}
                        ]
                    },
                     {
                        "questionId": "q_phy_02",
                        "questionText": "What is the value of g?",
                        "questionImageUrl": None,
                        "type": "NUMERICAL",
                        "positiveMarks": 4,
                        "negativeMarks": 0,
                        "options": []
                    }
                ]
            },
            {
                "sectionId": "chem_sec_1",
                "sectionName": "Chemistry Sec 1",
                "questions": [
                    {
                        "questionId": "q_chem_01",
                        "questionText": "What is the chemical symbol for Gold?",
                        "questionImageUrl": None,
                        "type": "MCQ",
                        "positiveMarks": 4,
                        "negativeMarks": -1,
                        "options": [
                            {"optionId": "opt_c1_a", "optionText": "Ag", "optionImageUrl": None},
                            {"optionId": "opt_c1_b", "optionText": "Au", "optionImageUrl": None},
                            {"optionId": "opt_c1_c", "optionText": "Fe", "optionImageUrl": None},
                            {"optionId": "opt_c1_d", "optionText": "Pb", "optionImageUrl": None}
                        ]
                    }
                ]
            }
        ]
    }