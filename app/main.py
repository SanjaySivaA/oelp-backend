import re  # Add this import at the top
from sqlalchemy import select, func  # Add func for random ordering
from fastapi import FastAPI, Depends, HTTPException, status, Request
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

import json
from typing import List, Any 

from pathlib import Path

from fastapi.middleware.cors import CORSMiddleware


from fastapi.responses import JSONResponse # NEW: Import JSONResponse
from fastapi.exceptions import RequestValidationError # NEW: Import the validation error
import traceback
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
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print("\n--- [CRITICAL VALIDATION ERROR] ---")
    print(f"Endpoint: {request.method} {request.url.path}")
    # exc.errors() is a list of dictionaries explaining the validation failure
    print(json.dumps(exc.errors(), indent=2))
    print("-------------------------------------\n")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )
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

# @app.get("/getTest", response_model=schemas.TestResponse)
# async def get_test_from_json(
#     db: AsyncSession = Depends(get_db),
#     current_user: models.User = Depends(get_current_user)
# ):
#     try:
#         base_dir = Path(__file__).resolve().parent.parent
#         json_file_path = base_dir / "assets" / "2017_1.json"
#         with open(json_file_path, 'r', encoding='utf-8') as f:
#             questions_data = json.load(f)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Critical error reading questions file: {e}")

#     # Create and save a new Test record in the database first.
#     new_test = models.Test(
#         test_id=str(uuid.uuid4()),
#         user_id=current_user.user_id,
#         test_name="Practice Test from JSON",
#         test_type=models.TestTypeEnum.CUSTOM,
#         status=models.TestStatusEnum.IN_PROGRESS,
#         start_time=datetime.utcnow()
#     )
#     db.add(new_test)
#     await db.commit()
#     await db.refresh(new_test) # Load the new ID from the DB

#     # Now, format the JSON questions for the frontend
#     sections_map = {}
#     for i, q_json in enumerate(questions_data):
#         q_type = (q_json.get("question_type") or "UNKNOWN").strip()
#         if q_type not in sections_map: sections_map[q_type] = []
        
#         options = []
#         if q_json.get("option_A"): options.append({"optionId": str(uuid.uuid4()), "optionText": q_json.get("option_A")})
#         if q_json.get("option_B"): options.append({"optionId": str(uuid.uuid4()), "optionText": q_json.get("option_B")})
#         if q_json.get("option_C"): options.append({"optionId": str(uuid.uuid4()), "optionText": q_json.get("option_C")})
#         if q_json.get("option_D"): options.append({"optionId": str(uuid.uuid4()), "optionText": q_json.get("option_D")})
            
#         sections_map[q_type].append({
#             "questionId": f"q_{i}",
#             "questionText": q_json.get("question_text"),
#             "options": options,
#             "positiveMarks": q_json.get("positive_marks"),
#             "negativeMarks": q_json.get("negative_marks")
#         })

#     final_sections = [
#         {"sectionId": f"{qt.lower()}_sec", "sectionName": f"Section - {qt}", "questionType": qt, "questions": qs}
#         for qt, qs in sections_map.items()
#     ]

#     # THIS IS THE FIX: Return the REAL ID that was saved to the database.
#     return {
#         "sessionId": new_test.test_id,
#         "testId": new_test.test_id,
#         "testName": new_test.test_name,
#         "durationInSeconds": 3600,
#         "sections": final_sections
#     }

# @app.post("/tests/{test_id}/submit", response_model=schemas.TestSubmissionResponse)
# async def submit_database_test(
#     test_id: str,
#     submission: schemas.TestSubmissionRequest,
#     db: AsyncSession = Depends(get_db),
#     current_user: models.User = Depends(get_current_user)
# ):
#     try:
#         # 1. Fetch the test and all its related questions/options FROM THE DATABASE
#         test_query = (
#             select(models.Test)
#             .where(models.Test.test_id == test_id, models.Test.user_id == current_user.user_id)
#             .options(selectinload(models.Test.answers).selectinload(models.TestAnswer.question).options(selectinload(models.Question.options), selectinload(models.Question.subtopic).selectinload(models.Subtopic.chapter).selectinload(models.Chapter.subject)))
#         )
#         test = (await db.execute(test_query)).scalars().first()

#         if not test: raise HTTPException(status_code=404, detail="Test session not found.")
#         if test.status == models.TestStatusEnum.COMPLETED: raise HTTPException(status_code=400, detail="This test has already been submitted.")

#         # 2. Score the test
#         final_score, max_score = 0, 0
#         answers_map = {ans.questionId: ans for ans in submission.answers}
#         subject_analytics_updates = {}

#         for test_answer in test.answers:
#             question = test_answer.question
#             max_score += question.positive_marks
            
#             subject = question.subtopic.chapter.subject
#             if subject.subject_name not in subject_analytics_updates:
#                 subject_analytics_updates[subject.subject_name] = {"correct": 0, "attempted": 0, "time": 0, "subject_id": subject.subject_id}
            
#             subject_analytics_updates[subject.subject_name]["attempted"] += 1

#             user_submission = answers_map.get(question.question_id)
#             if not user_submission or not user_submission.selectedOptionIds:
#                 test_answer.status = models.TestAnswerStatusEnum.UNATTEMPTED
#                 continue
            
#             # THIS IS THE FIX: Compare the sets of IDs directly from the database.
#             correct_option_ids = {opt.option_id for opt in question.options if opt.is_correct}
#             selected_option_ids = set(user_submission.selectedOptionIds)
#             is_correct = (correct_option_ids == selected_option_ids)
            
#             if is_correct:
#                 final_score += question.positive_marks
#                 test_answer.status = models.TestAnswerStatusEnum.CORRECT
#                 subject_analytics_updates[subject.subject_name]["correct"] += 1
#             else:
#                 final_score += question.negative_marks
#                 test_answer.status = models.TestAnswerStatusEnum.INCORRECT

#         # 3. Update the main Test record
#         test.final_score = final_score
#         test.status = models.TestStatusEnum.COMPLETED
#         test.end_time = datetime.utcnow()

#         # 4. Update the analytics tables
#         for subject_name, updates in subject_analytics_updates.items():
#             stmt = text(""" (Your correct analytics SQL statement) """)
#             await db.execute(stmt, { #... (Your correct params)
#             })
        
#         await db.commit()
        
#         return {"message": "Test submitted successfully!", "testId": test_id, "finalScore": final_score, "maxScore": float(max_score)}

#     except Exception as e:
#         await db.rollback()
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")

@app.get("/getTest", response_model=schemas.TestResponse)
async def create_test_from_db(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        # 1. Fetch random questions from the database WITH EAGER LOADING
        print("[DEBUG /getTest] Fetching questions...") # Debug
        questions_query = (
            select(models.Question)
            .order_by(func.random())
            .limit(54)
            .options(selectinload(models.Question.options)) # Eager load options
        )
        questions_result = await db.execute(questions_query)
        questions = questions_result.scalars().all()
        if not questions:
            raise HTTPException(status_code=404, detail="No questions found in database.")
        print(f"[DEBUG /getTest] Fetched {len(questions)} questions.") # Debug

        # 2. IMMEDIATELY Format the response data WHILE THE SESSION IS ACTIVE
        # This prevents the MissingGreenlet error by accessing attributes now.
        print("[DEBUG /getTest] Formatting response sections...") # Debug
        sections_map = {}
        for q in questions:
            # Access attributes needed for the response *now*
            q_type = q.question_type.value if q.question_type else "UNKNOWN"
            question_id = q.question_id
            question_text = q.question_text
            positive_marks = q.positive_marks
            negative_marks = q.negative_marks
            options_list = [{"optionId": opt.option_id, "optionText": opt.option_text} for opt in q.options]

            if q_type not in sections_map: sections_map[q_type] = []
            sections_map[q_type].append({
                "questionId": question_id, "questionText": question_text,
                "options": options_list,
                "positiveMarks": positive_marks, "negativeMarks": negative_marks
            })
        
        final_sections = [
            {"sectionId": f"{qt.lower()}_sec", "sectionName": f"Section - {qt}", "questionType": qt, "questions": qs}
            for qt, qs in sections_map.items()
        ]
        print("[DEBUG /getTest] Response sections formatted.") # Debug

        # 3. Create and save the new Test session record
        print("[DEBUG /getTest] Creating Test record in DB...") # Debug
        new_test = models.Test(
            test_id=str(uuid.uuid4()), user_id=current_user.user_id,
            test_name="Dynamic Practice Test", test_type=models.TestTypeEnum.CUSTOM,
            status=models.TestStatusEnum.IN_PROGRESS, start_time=datetime.utcnow()
        )
        db.add(new_test)
        
        # 4. Create the placeholder TestAnswer records
        # We use the question objects directly fetched earlier
        print("[DEBUG /getTest] Creating placeholder TestAnswer records...") # Debug
        answers_to_add = [
            models.TestAnswer(answer_id=str(uuid.uuid4()), test=new_test, question=question)
            for question in questions
        ]
        db.add_all(answers_to_add)
        
        print("[DEBUG /getTest] Committing Test and TestAnswers...") # Debug
        await db.commit()
        await db.refresh(new_test) # Refresh to ensure ID is loaded
        print("[DEBUG /getTest] Commit successful.") # Debug

        # 5. Return the formatted data
        return {
            "sessionId": new_test.test_id, "testId": new_test.test_id,
            "testName": new_test.test_name, "durationInSeconds": 3600,
            "sections": final_sections
        }
    except Exception as e:
        # Provide more context in case of error
        print("\n--- ERROR IN /getTest ---")
        traceback.print_exc()
        print("-------------------------\n")
        # Ensure rollback occurs if commit failed
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating test: {e}")

@app.post("/tests/{test_id}/submit", response_model=schemas.TestSubmissionResponse)
async def submit_database_test(
    test_id: str,
    submission: schemas.TestSubmissionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        # 1. Fetch the test and all its related data FROM THE DATABASE
        test_query = (
            select(models.Test)
            .where(models.Test.test_id == test_id, models.Test.user_id == current_user.user_id)
            .options(
                # Eager load everything needed for scoring and analytics
                selectinload(models.Test.answers)
                .selectinload(models.TestAnswer.question)
                .options(
                    selectinload(models.Question.options), # Need options for correct answer check
                    selectinload(models.Question.subtopic) # Need subtopic -> chapter -> subject for analytics
                    .selectinload(models.Subtopic.chapter)
                    .selectinload(models.Chapter.subject)
                )
            )
        )
        test = (await db.execute(test_query)).scalars().first()

        if not test: raise HTTPException(status_code=404, detail="Test session not found.")
        if test.status == models.TestStatusEnum.COMPLETED: raise HTTPException(status_code=400, detail="This test has already been submitted.")

        # 2. Score the test
        final_score, max_score = 0, 0
        answers_map = {ans.questionId: ans for ans in submission.answers}
        subject_analytics_updates = {}

        print("\n--- [DEBUG] Starting Score Calculation ---") # DEBUG
        for test_answer in test.answers:
            question = test_answer.question
            if not question: # Safety check
                print(f"  [WARN] Skipping TestAnswer {test_answer.answer_id} due to missing Question link.")
                continue
                
            max_score += question.positive_marks
            
            # Safely get subject info
            subject = None
            if question.subtopic and question.subtopic.chapter and question.subtopic.chapter.subject:
                 subject = question.subtopic.chapter.subject
                 if subject.subject_name not in subject_analytics_updates:
                     subject_analytics_updates[subject.subject_name] = {"correct": 0, "attempted": 0, "time": 0, "subject_id": subject.subject_id}
                 subject_analytics_updates[subject.subject_name]["attempted"] += 1
            else:
                 print(f"  [WARN] Cannot find subject for Question {question.question_id}. Skipping analytics update for this question.")


            user_submission = answers_map.get(question.question_id)
            
            # --- Evaluation Logic ---
            is_correct = False # Default to incorrect
            selected_option_ids = set()
            
            if user_submission and user_submission.selectedOptionIds:
                selected_option_ids = set(user_submission.selectedOptionIds)
                
                # Get correct IDs directly from the database objects
                correct_option_ids = {opt.option_id for opt in question.options if opt.is_correct}
                
                # =======================================================================
                # THIS IS THE FIX: The comparison logic is now correct.
                # =======================================================================
                is_correct = (correct_option_ids == selected_option_ids)

                print(f"  Q: {question.question_id[:8]}...") # DEBUG
                print(f"    Correct IDs : {sorted(list(correct_option_ids))}") # DEBUG
                print(f"    Selected IDs: {sorted(list(selected_option_ids))}") # DEBUG
                print(f"    Result      : {'CORRECT' if is_correct else 'INCORRECT'}") # DEBUG
            
            # --- Update Score and Status ---
            if not user_submission or not user_submission.selectedOptionIds:
                test_answer.status = models.TestAnswerStatusEnum.UNATTEMPTED
                print(f"  Q: {question.question_id[:8]}... Unattempted") # DEBUG
            elif is_correct:
                final_score += question.positive_marks
                test_answer.status = models.TestAnswerStatusEnum.CORRECT
                if subject: subject_analytics_updates[subject.subject_name]["correct"] += 1
            else:
                final_score += question.negative_marks
                test_answer.status = models.TestAnswerStatusEnum.INCORRECT

        print(f"--- [DEBUG] Score Calculation Complete. Final Score: {final_score} ---") # DEBUG

        # 3. Update the main Test record
        test.final_score = final_score
        test.status = models.TestStatusEnum.COMPLETED
        test.end_time = datetime.utcnow()

        # 4. Update the analytics tables
        print("--- [DEBUG] Updating Analytics Tables ---") # DEBUG
        for subject_name, updates in subject_analytics_updates.items():
            print(f"  Updating analytics for {subject_name}: Attempted={updates['attempted']}, Correct={updates['correct']}") # DEBUG
            stmt = text("""
                INSERT INTO user_subject_analytics (user_id, exam_id, subject_id, questions_attempted, correct_answers, total_time_taken_seconds, last_updated_at)
                VALUES (:user_id, :exam_id, :subject_id, :attempted, :correct, :time_taken, :now)
                ON CONFLICT (user_id, exam_id, subject_id) DO UPDATE SET
                questions_attempted = user_subject_analytics.questions_attempted + :attempted,
                correct_answers = user_subject_analytics.correct_answers + :correct,
                total_time_taken_seconds = user_subject_analytics.total_time_taken_seconds + :time_taken,
                last_updated_at = :now;
            """)
            await db.execute(stmt, {
                "user_id": current_user.user_id, "exam_id": 1, "subject_id": updates["subject_id"],
                "attempted": updates["attempted"], "correct": updates["correct"],
                "time_taken": updates["time"], "now": datetime.utcnow()
            })
        print("--- [DEBUG] Analytics Update Complete ---") # DEBUG

        print("--- [DEBUG] Committing Transaction ---") # DEBUG
        await db.commit()
        print("--- [DEBUG] Commit Successful ---") # DEBUG
        
        return {"message": "Test submitted successfully!", "testId": test_id, "finalScore": final_score, "maxScore": float(max_score)}

    except Exception as e:
        # Ensure rollback happens on any error
        await db.rollback()
        traceback.print_exc() # Print full error for debugging
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")
    
@app.get("/analytics", response_model=schemas.AnalyticsResponse)
async def get_analytics_data(
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_id = current_user.user_id

    # --- Query 1: Stats Cards ---
    completed_tests_query = select(func.count(models.Test.test_id)).where(
        models.Test.user_id == user_id,
        models.Test.status == models.TestStatusEnum.COMPLETED
    )
    completed_tests_count_result = await db.execute(completed_tests_query)
    completed_tests_count = completed_tests_count_result.scalar_one_or_none() or 0

    # --- Query 2: Average Accuracy ---
    accuracy_query = select(
        func.sum(models.UserSubjectAnalytics.correct_answers),
        func.sum(models.UserSubjectAnalytics.questions_attempted)
    ).where(models.UserSubjectAnalytics.user_id == user_id)
    accuracy_result = await db.execute(accuracy_query)
    total_correct, total_attempted = accuracy_result.first() or (0, 0)
    average_accuracy = (total_correct / total_attempted * 100) if total_attempted else 0.0

    stats_cards = [
        schemas.StatsCardData(title="Total Tests Completed", value=str(completed_tests_count), change="", trend_color="green"),
        schemas.StatsCardData(title="Average Accuracy", value=f"{average_accuracy:.1f}%", change="", trend_color="green"),
    ]

    # --- Query 3: Score Progression ---
    score_progression_query = (
        select(models.Test.final_score, models.Test.end_time)
        .where(models.Test.user_id == user_id, models.Test.status == models.TestStatusEnum.COMPLETED, models.Test.final_score.is_not(None))
        .order_by(models.Test.end_time.asc()).limit(7)
    )
    score_results = (await db.execute(score_progression_query)).all()
    test_score_progression = schemas.TestScoreProgressionData(
        spots=[schemas.ChartSpot(x=float(i), y=score) for i, (score, _) in enumerate(score_results)],
        dates=[dt.strftime("%b %d") for _, dt in score_results]
    )

    # --- Query 4: Subject Performance ---
    subject_perf_query = (
        select(models.Subject.subject_name, models.UserSubjectAnalytics.correct_answers, models.UserSubjectAnalytics.questions_attempted)
        .join(models.Subject, models.UserSubjectAnalytics.subject_id == models.Subject.subject_id)
        .where(models.UserSubjectAnalytics.user_id == user_id)
    )
    subject_perf_results = (await db.execute(subject_perf_query)).all()
    subject_performance = [
        schemas.SubjectPerformanceData(subject_name=name, accuracy=(correct / attempted * 100) if attempted else 0)
        for name, correct, attempted in subject_perf_results
    ]

    # --- Query 5: Recent Tests ---
    recent_tests_query = (
        select(models.Test)
        .where(models.Test.user_id == user_id, models.Test.status == models.TestStatusEnum.COMPLETED)
        .order_by(models.Test.end_time.desc()).limit(4)
        .options(selectinload(models.Test.subject))
    )
    recent_tests_results = (await db.execute(recent_tests_query)).scalars().all()
    
    recent_tests = []
    for test in recent_tests_results:
        duration_delta = test.end_time - test.start_time if test.end_time and test.start_time else timedelta(0)
        duration_mins = duration_delta.total_seconds() // 60
        
        recent_tests.append(schemas.RecentTestData(
            name=test.test_name, subject=test.subject.subject_name if test.subject else "Mixed",
            score=int(test.final_score) if test.final_score is not None else 0,
            max_score=180, # Placeholder
            status=test.status.value,
            date=test.end_time.strftime("%b %d, %Y") if test.end_time else "N/A",
            time=f"{int(duration_mins)} mins"
        ))

    # Construct the final response object
    response_data = schemas.AnalyticsResponse(
        username=current_user.name, stats_cards=stats_cards,
        test_score_progression=test_score_progression,
        subject_performance=subject_performance,
        recent_tests=recent_tests,
    )

    # =======================================================================
    # THE BLACK BOX RECORDER: This will print the exact data being sent.
    # =======================================================================
    print("\n--- [ANALYTICS RESPONSE DATA SENT TO FLUTTER] ---")
    # We use model_dump_json for a clean, indented print of the Pydantic model
    print(response_data.model_dump_json(indent=2))
    print("--------------------------------------------------\n")

    return response_data

# =======================================================================
# NEW: QUESTIONS ENDPOINT
# =======================================================================
@app.get("/questions", response_model=List[Any])
async def get_questions(current_user: models.User = Depends(get_current_user)):
    """
    Reads the questions from a JSON file and returns them.
    This endpoint is protected and requires user authentication.
    """
    try:
        # The path is relative to where you run uvicorn (the oelp-backend folder)
        with open('assets/2017_1.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Questions file not found on the server."
        )
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error decoding the questions JSON file."
        )

# =======================================================================
# NEW: TEST SUBMISSION AND EVALUATION ENDPOINT
# =======================================================================
@app.post("/tests/submit", response_model=schemas.TestSubmissionResponse)
async def submit_json_test(
    submission: schemas.TestSubmissionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        base_dir = Path(__file__).resolve().parent.parent
        json_file_path = base_dir / "assets" / "2017_1.json"
        with open(json_file_path, 'r', encoding='utf-8') as f:
            questions_data = json.load(f)
        
        final_score, max_score = 0, sum(q.get("positive_marks", 0) for q in questions_data)
        answers_map = {ans.questionId: ans for ans in submission.answers}

        for i, question_details in enumerate(questions_data):
            question_id = f"q_{i}"
            user_submission = answers_map.get(question_id)

            if not user_submission or not user_submission.selectedOptionIds:
                continue
            
            correct_option_str = question_details.get("correct_option")
            correct_option_texts = set()
            if correct_option_str:
                correct_letters = [letter.strip() for letter in correct_option_str.split(',')]
                correct_option_texts = {question_details.get(f"option_{l}") for l in correct_letters if question_details.get(f"option_{l}")}

            selected_option_texts = set(user_submission.selectedOptionIds)

            if correct_option_texts == selected_option_texts:
                final_score += question_details.get("positive_marks", 0)
            else:
                final_score += question_details.get("negative_marks", 0)
        
        completed_test = models.Test(
            test_id=submission.sessionId, user_id=current_user.user_id,
            test_name="Practice Test from JSON", test_type=models.TestTypeEnum.CUSTOM,
            status=models.TestStatusEnum.COMPLETED,
            start_time=datetime.utcnow() - timedelta(minutes=60),
            end_time=datetime.utcnow(), final_score=final_score
        )
        db.add(completed_test)
        await db.commit()
        
        return {"message": "Test submitted successfully!", "testId": submission.sessionId, "finalScore": final_score, "maxScore": float(max_score)}

    except Exception as e:
        await db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")