import re  # Add this import at the top
from sqlalchemy import select, func  # Add func for random ordering
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import uuid
from sqlalchemy import select
from . import rag_routes
from .auth import get_current_user
from sqlalchemy.orm import selectinload # Efficiently load related options
from sqlalchemy.orm import selectinload
from sqlalchemy import func, case, text

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
    allow_origins=settings.ALLOWED_ORIGINS, # Or, allow all origins
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

@app.get("/users/me", response_model=schemas.UserPublic)
async def read_users_me(current_user: models.User = Depends(get_current_user)): # This line now works
    return current_user

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



# =======================================================================
# 1. ANALYTICS DATA ENDPOINT
# =======================================================================
@app.get("/analytics", response_model=schemas.AnalyticsResponse)
async def get_analytics_data(
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Provides all necessary data to populate the user's analytics dashboard.
    """
    user_id = current_user.user_id

    # --- Query 1: Stats Cards ---
    # Total tests completed
    completed_tests_query = select(func.count(models.Test.test_id)).where(
        models.Test.user_id == user_id,
        models.Test.status == models.TestStatusEnum.COMPLETED
    )
    completed_tests_count = (await db.execute(completed_tests_query)).scalar_one()

    # Average accuracy from aggregate table
    accuracy_query = select(
        func.sum(models.UserSubjectAnalytics.correct_answers),
        func.sum(models.UserSubjectAnalytics.questions_attempted)
    ).where(models.UserSubjectAnalytics.user_id == user_id)
    accuracy_result = (await db.execute(accuracy_query)).first()
    
    total_correct, total_attempted = accuracy_result or (0, 0)
    average_accuracy = (total_correct / total_attempted * 100) if total_attempted else 0.0

    # For now, let's use dummy values for "change" and "study time" as they require historical data
    stats_cards = [
        schemas.StatsCardData(title="Total Tests Completed", value=str(completed_tests_count), change="+12% from last month", trend_color="green"),
        schemas.StatsCardData(title="Average Accuracy", value=f"{average_accuracy:.1f}%", change="+5% from last month", trend_color="green"),
        schemas.StatsCardData(title="Study Time This Week", value="24.5h", change="-2% from last week", trend_color="red"),
        schemas.StatsCardData(title="Overall Progress", value="92%", change="+8% from last month", trend_color="green"),
    ]

    # --- Query 2: Test Score Progression (Line Chart) ---
    # Fetch the last 7 completed tests
    score_progression_query = (
        select(models.Test.final_score, models.Test.end_time)
        .where(
            models.Test.user_id == user_id,
            models.Test.status == models.TestStatusEnum.COMPLETED,
            models.Test.final_score.is_not(None) # Ensure score exists
        )
        .order_by(models.Test.end_time.asc())
        .limit(7)
    )
    score_results = (await db.execute(score_progression_query)).all()
    
    test_score_progression = schemas.TestScoreProgressionData(
        spots=[schemas.ChartSpot(x=float(i), y=score) for i, (score, _) in enumerate(score_results)],
        dates=[dt.strftime("%b %d") for _, dt in score_results]
    )

    # --- Query 3: Subject Performance (Bar Chart & Progress Bars) ---
    subject_perf_query = (
        select(
            models.Subject.subject_name,
            models.UserSubjectAnalytics.correct_answers,
            models.UserSubjectAnalytics.questions_attempted
        )
        .join(models.Subject, models.UserSubjectAnalytics.subject_id == models.Subject.subject_id)
        .where(models.UserSubjectAnalytics.user_id == user_id)
    )
    subject_perf_results = (await db.execute(subject_perf_query)).all()

    subject_performance = [
        schemas.SubjectPerformanceData(
            subject_name=name,
            accuracy=(correct / attempted * 100) if attempted else 0
        ) for name, correct, attempted in subject_perf_results
    ]

    # --- Query 4: Recent Tests List ---
    # This is a more complex query as we need to calculate max score on the fly.
    # NOTE: For better performance, consider adding a `max_score` column to the `Test` table.
    recent_tests_query = (
        select(models.Test)
        .options(selectinload(models.Test.subject), selectinload(models.Test.answers).selectinload(models.TestAnswer.question))
        .where(
            models.Test.user_id == user_id,
            models.Test.status == models.TestStatusEnum.COMPLETED
        )
        .order_by(models.Test.end_time.desc())
        .limit(4)
    )
    recent_tests_results = (await db.execute(recent_tests_query)).scalars().all()
    
    recent_tests = []
    for test in recent_tests_results:
        max_score = sum(ans.question.positive_marks for ans in test.answers)
        duration_delta = test.end_time - test.start_time
        duration_mins = duration_delta.total_seconds() // 60
        
        recent_tests.append(schemas.RecentTestData(
            name=test.test_name,
            subject=test.subject.subject_name if test.subject else "Mixed",
            score=int(test.final_score),
            max_score=max_score,
            status=test.status.value,
            date=test.end_time.strftime("%b %d, %Y"),
            time=f"{int(duration_mins)} mins"
        ))

    return schemas.AnalyticsResponse(
        username=current_user.name,
        stats_cards=stats_cards,
        test_score_progression=test_score_progression,
        subject_performance=subject_performance,
        recent_tests=recent_tests,
    )


# =======================================================================
# 2. TEST CALCULATION & SUBMISSION ENDPOINT
# =======================================================================
@app.post("/tests/{test_id}/submit", response_model=schemas.TestSubmissionResponse)
async def submit_test(
    test_id: str,
    submission: schemas.TestSubmissionRequest,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Receives user's answers for a test, calculates the score, updates analytics,
    and marks the test as completed.
    """
    # --- Step 1: Fetch the test and ensure it's valid to submit ---
    test_query = (
        select(models.Test)
        .options(
            selectinload(models.Test.answers).selectinload(models.TestAnswer.question).options(
                selectinload(models.Question.options),
                selectinload(models.Question.subtopic).selectinload(models.Subtopic.chapter).selectinload(models.Chapter.subject)
            )
        )
        .where(models.Test.test_id == test_id, models.Test.user_id == current_user.user_id)
    )
    test = (await db.execute(test_query)).scalars().first()

    if not test:
        raise HTTPException(status_code=404, detail="Test not found.")
    if test.status == models.TestStatusEnum.COMPLETED:
        raise HTTPException(status_code=400, detail="Test has already been completed.")

    # --- Step 2: Process and score each answer ---
    final_score = 0
    max_score = 0
    answers_map = {ans.question_id: ans for ans in submission.answers}
    
    # Dictionaries to aggregate analytics updates
    subject_analytics_updates = {} # {subject_id: {"correct": x, "attempted": y, "time": z}}
    
    for test_answer in test.answers:
        question = test_answer.question
        max_score += question.positive_marks
        
        user_submission = answers_map.get(question.question_id)
        
        # If the user didn't submit an answer for this question
        if not user_submission or (not user_submission.selected_option_ids and user_submission.integer_answer is None):
            test_answer.status = models.TestAnswerStatusEnum.UNATTEMPTED
            continue # No score change

        # --- Update the TestAnswer record ---
        test_answer.time_taken_seconds = user_submission.time_taken_seconds
        
        # --- Scoring Logic ---
        is_correct = False
        if question.question_type in [models.QuestionType.MCSC, models.QuestionType.MCMC]:
            correct_option_ids = {opt.option_id for opt in question.options if opt.is_correct}
            selected_option_ids = set(user_submission.selected_option_ids or [])
            
            # Update selections in DB
            test_answer.selections = [
                models.TestAnswerSelection(selected_option_id=opt_id) for opt_id in selected_option_ids
            ]
            
            if correct_option_ids == selected_option_ids:
                is_correct = True
        
        elif question.question_type in [models.QuestionType.INT, models.QuestionType.NUM]:
            # For numerical, we assume the solution is stored in the first option's text
            # A better design would be a dedicated `correct_answer_text` field in the Question model
            correct_answer = int(question.options[0].option_text) if question.options else None
            test_answer.integer_answer = user_submission.integer_answer
            if correct_answer is not None and user_submission.integer_answer == correct_answer:
                is_correct = True
        
        # --- Apply marks and update status ---
        if is_correct:
            final_score += question.positive_marks
            test_answer.status = models.TestAnswerStatusEnum.CORRECT
        else:
            final_score -= question.negative_marks
            test_answer.status = models.TestAnswerStatusEnum.INCORRECT
            
        # --- Aggregate analytics ---
        sub_id = question.subtopic.chapter.subject_id
        if sub_id not in subject_analytics_updates:
            subject_analytics_updates[sub_id] = {"correct": 0, "attempted": 0, "time": 0}

        subject_analytics_updates[sub_id]["attempted"] += 1
        subject_analytics_updates[sub_id]["time"] += user_submission.time_taken_seconds
        if is_correct:
            subject_analytics_updates[sub_id]["correct"] += 1

    # --- Step 3: Update the main Test record ---
    test.final_score = final_score
    test.status = models.TestStatusEnum.COMPLETED
    test.end_time = datetime.utcnow()

    # --- Step 4: Update aggregate analytics tables ---
    # This part can be slow if done naively. A bulk update or a database-side
    # procedure would be more efficient for high traffic.
    for subject_id, updates in subject_analytics_updates.items():
        # Find existing record or create a new one (UPSERT logic)
        analytics_record_query = select(models.UserSubjectAnalytics).where(
            models.UserSubjectAnalytics.user_id == current_user.user_id,
            models.UserSubjectAnalytics.subject_id == subject_id,
            # Assuming exam_id=1 for now, you'll need to pass this in a real scenario
            models.UserSubjectAnalytics.exam_id == 1 
        )
        record = (await db.execute(analytics_record_query)).scalars().first()
        
        if record:
            record.correct_answers += updates["correct"]
            record.questions_attempted += updates["attempted"]
            record.total_time_taken_seconds += updates["time"]
        else:
            new_record = models.UserSubjectAnalytics(
                user_id=current_user.user_id,
                exam_id=1, # Replace with actual exam_id
                subject_id=subject_id,
                correct_answers=updates["correct"],
                questions_attempted=updates["attempted"],
                total_time_taken_seconds=updates["time"]
            )
            db.add(new_record)
            
    await db.commit()

    return schemas.TestSubmissionResponse(
        message="Test submitted successfully",
        test_id=test_id,
        final_score=final_score,
        max_score=float(max_score)
    )
