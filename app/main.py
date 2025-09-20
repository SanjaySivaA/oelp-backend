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
    # allow_origins=settings.ALLOWED_ORIGINS, # <-- We are replacing this line
    allow_origin_regex=settings.CORS_ORIGIN_REGEX, # <-- With this new line
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    """
    Dependency to get the current user from a JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the JWT
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # The "sub" (subject) of our token is the user's email
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        # If the token is invalid for any reason, raise the exception
        raise credentials_exception
    
    # Find the user in the database
    user_result = await db.execute(select(models.User).where(models.User.email == token_data.email))
    user = user_result.scalars().first()
    
    if user is None:
        # If the user from the token doesn't exist in the DB, raise the exception
        raise credentials_exception
    
    return user

# --- Endpoints ---

@app.post("/register", response_model=schemas.RegisterResponse)
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
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.email}, expires_delta=access_token_expires
    )
    
    return {
        "user_info": new_user,
        "token": {"access_token": access_token, "token_type": "bearer"}
    }

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

@app.get("/users/me", response_model=schemas.UserPublic)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    """
    Fetch the currently authenticated user's data.
    """
    # The get_current_user dependency has already done all the work of
    # validating the token and fetching the user from the database.
    # If the token was bad, this code would never even be reached.
    # We just need to return the user object.
    return current_user

@app.get("/getTest")
async def sendTest():
    return {
        "sessionId": "session_mock_12345",
        "testId": "jee_main_mock_01",
        "testName": "Test",
        "durationInSeconds": 3600, # 1 hour
        "sections": [
            {
                "sectionId": "phy_sec_1",
                "sectionName": "Physics Sec 1",
                "type": "MCSC",
                "positiveMarks": 4,
                "negativeMarks": -1,
                "questions": [
                    {
                        "questionId": "q_phy_01",
                        "questionText": "What is the unit of **force**?\n\n ![The Man](https://en.wikipedia.org/wiki/Force#/media/File:GodfreyKneller-IsaacNewton-1689.jpg)",
                        "questionImageUrl": None,
                        "options": [
                            {"optionId": "opt_p1_a", "optionText": "Newton", "optionImageUrl": None},
                            {"optionId": "opt_p1_b", "optionText": "Watt", "optionImageUrl": None},
                            {"optionId": "opt_p1_c", "optionText": "Joule", "optionImageUrl": None},
                            {"optionId": "opt_p1_d", "optionText": "Pascal", "optionImageUrl": None}
                        ]
                    }
                ]
            },
            {
                "sectionId": "phy_sec_2",
                "sectionName": "Physics Sec 2",
                "type": "NUMERICAL",
                "positiveMarks": 4,
                "negativeMarks": 0,
                "questions": [
                {
                        "questionId": "q_phy_02",
                        "questionText": "What is the value of **g**?",
                        "questionImageUrl": None,
                        "options": []
                    }
                ]
            },
            {
                "sectionId": "phy_sec_3",
                "sectionName": "Physics Sec 3",
                "type": "MCMC",
                "positiveMarks": 4,
                "negativeMarks": -2,
                "questions": [
                {
                        "questionId": "q_phy_03",
                        "questionText": "What is the unit of **force**?",
                        "questionImageUrl": None,
                        "options": [
                            {"optionId": "opt_p3_a", "optionText": "Newton", "optionImageUrl": None},
                            {"optionId": "opt_p3_b", "optionText": "N", "optionImageUrl": None},
                            {"optionId": "opt_p3_c", "optionText": "Joule", "optionImageUrl": None},
                            {"optionId": "opt_p3_d", "optionText": "Pascal", "optionImageUrl": None}
                        ]
                    }
                ]
            },
            {
                "sectionId": "chem_sec_1",
                "sectionName": "Chemistry Sec 1",
                "type": "MCSC",
                "positiveMarks": 4,
                "negativeMarks": -1,
                "questions": [
                    {
                        "questionId": "q_chem_01",
                        "questionText": "What is the chemical symbol for Gold?",
                        "questionImageUrl": None,
                        "options": [
                            {"optionId": "opt_c1_a", "optionText": "Ag", "optionImageUrl": None},
                            {"optionId": "opt_c1_b", "optionText": "Au", "optionImageUrl": None},
                            {"optionId": "opt_c1_c", "optionText": "Fe", "optionImageUrl": None},
                            {"optionId": "opt_c1_d", "optionText": "Pb", "optionImageUrl": None}
                        ]
                    },
                    {
                        "questionId": "q_chem_02",
                        "questionText": "What is the chemical symbol for Gold?",
                        "questionImageUrl": None,
                        "options": [
                            {"optionId": "opt_c2_a", "optionText": "Ag", "optionImageUrl": None},
                            {"optionId": "opt_c2_b", "optionText": "Au", "optionImageUrl": None},
                            {"optionId": "opt_c2_c", "optionText": "Fe", "optionImageUrl": None},
                            {"optionId": "opt_c2_d", "optionText": "Pb", "optionImageUrl": None}
                        ]
                    },
                    {
                        "questionId": "q_chem_03",
                        "questionText": "What is the chemical symbol for Gold?",
                        "questionImageUrl": None,
                        "options": [
                            {"optionId": "opt_c3_a", "optionText": "Ag", "optionImageUrl": None},
                            {"optionId": "opt_c3_b", "optionText": "Au", "optionImageUrl": None},
                            {"optionId": "opt_c3_c", "optionText": "Fe", "optionImageUrl": None},
                            {"optionId": "opt_c3_d", "optionText": "Pb", "optionImageUrl": None}
                        ]
                    },
                    {
                        "questionId": "q_chem_04",
                        "questionText": "What is the chemical symbol for Gold?",
                        "questionImageUrl": None,
                        "options": [
                            {"optionId": "opt_c4_a", "optionText": "Ag", "optionImageUrl": None},
                            {"optionId": "opt_c4_b", "optionText": "Au", "optionImageUrl": None},
                            {"optionId": "opt_c4_c", "optionText": "Fe", "optionImageUrl": None},
                            {"optionId": "opt_c4_d", "optionText": "Pb", "optionImageUrl": None}
                        ]
                    }
                ]
            }
        ]
    }