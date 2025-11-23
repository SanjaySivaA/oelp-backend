import re
from sqlalchemy import select, func
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import uuid
from sqlalchemy import select
# from . import rag_routes
from .auth import get_current_user
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
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import traceback

# --- Security & Hashing Setup ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI()

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
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

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print("\n--- [CRITICAL VALIDATION ERROR] ---")
    print(f"Endpoint: {request.method} {request.url.path}")
    print(json.dumps(exc.errors(), indent=2))
    print("-------------------------------------\n")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

# --- Endpoints ---

@app.post("/register", response_model=schemas.RegisterResponse)
async def register_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
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
async def read_users_me(current_user: models.User = Depends(get_current_user)): 
    return current_user

@app.post("/login", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
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

@app.get("/getTest", response_model=schemas.TestResponse)
async def create_test_from_db(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        # 1. Fetch random questions from the database WITH EAGER LOADING
        print("[DEBUG /getTest] Fetching questions...") 
        questions_query = (
            select(models.Question)
            .order_by(func.random())
            .limit(54)
            .options(selectinload(models.Question.options)) 
        )
        questions_result = await db.execute(questions_query)
        questions = questions_result.scalars().all()
        if not questions:
            raise HTTPException(status_code=404, detail="No questions found in database.")
        print(f"[DEBUG /getTest] Fetched {len(questions)} questions.")

        # 2. Format the response data
        print("[DEBUG /getTest] Formatting response sections...") 
        sections_map = {}
        for q in questions:
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
        print("[DEBUG /getTest] Response sections formatted.") 

        # 3. Create a dynamic TestTemplate (Required by new Schema)
        # We fetch the first available exam to link to.
        exam_result = await db.execute(select(models.Exam).limit(1))
        exam = exam_result.scalars().first()
        if not exam:
             # Fallback if no exam exists (unlikely in prod if seeded)
             raise HTTPException(status_code=500, detail="No exams found in database to link test to.")

        new_template = models.TestTemplate(
            template_id=str(uuid.uuid4()),
            owner_user_id=current_user.user_id,
            exam_id=exam.exam_id,
            template_name="Dynamic Practice Session",
            test_type=models.TestTypeEnum.CUSTOM,
            duration_minutes=60,
            is_public=False,
            created_at=datetime.now(timezone.utc)
        )
        db.add(new_template)
        # We flush here to make sure the template_id is available for the Test
        await db.flush()

        # 4. Create and save the new Test session record
        print("[DEBUG /getTest] Creating Test record in DB...") 
        new_test = models.Test(
            test_id=str(uuid.uuid4()), 
            user_id=current_user.user_id,
            template_id=new_template.template_id, # Link to our new dynamic template
            test_name="Dynamic Practice Test", 
            test_type=models.TestTypeEnum.CUSTOM,
            status=models.TestStatusEnum.IN_PROGRESS, 
            start_time=datetime.now(timezone.utc) # Use timezone aware datetime
        )
        db.add(new_test)
        
        # 5. Create the placeholder TestAnswer records
        print("[DEBUG /getTest] Creating placeholder TestAnswer records...") 
        answers_to_add = [
            models.TestAnswer(answer_id=str(uuid.uuid4()), test=new_test, question=question)
            for question in questions
        ]
        db.add_all(answers_to_add)
        
        print("[DEBUG /getTest] Committing Test and TestAnswers...") 
        await db.commit()
        await db.refresh(new_test) 
        print("[DEBUG /getTest] Commit successful.") 

        # 6. Return the formatted data
        return {
            "sessionId": new_test.test_id, "testId": new_test.test_id,
            "testName": new_test.test_name, "durationInSeconds": 3600,
            "sections": final_sections
        }
    except Exception as e:
        print("\n--- ERROR IN /getTest ---")
        traceback.print_exc()
        print("-------------------------\n")
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
                # NEW: Eager load the template to get the exam_id
                selectinload(models.Test.template),
                selectinload(models.Test.answers)
                .selectinload(models.TestAnswer.question)
                .options(
                    selectinload(models.Question.options),
                    selectinload(models.Question.subtopic)
                    .selectinload(models.Subtopic.chapter)
                    .selectinload(models.Chapter.subject)
                )
            )
        )
        test = (await db.execute(test_query)).scalars().first()

        if not test: raise HTTPException(status_code=404, detail="Test session not found.")
        if test.status == models.TestStatusEnum.COMPLETED: raise HTTPException(status_code=400, detail="This test has already been submitted.")

        # NEW: Get the correct exam_id from the linked template
        # We fallback to 3 (JEE Advanced) only if something is very wrong with the data
        current_exam_id = test.template.exam_id if test.template else 3

        # 2. Score the test
        final_score, max_score = 0, 0
        answers_map = {ans.questionId: ans for ans in submission.answers}
        subject_analytics_updates = {}

        print("\n--- [DEBUG] Starting Score Calculation ---")
        for test_answer in test.answers:
            question = test_answer.question
            if not question:
                continue
                
            max_score += question.positive_marks
            
            subject = None
            if question.subtopic and question.subtopic.chapter and question.subtopic.chapter.subject:
                 subject = question.subtopic.chapter.subject
                 if subject.subject_name not in subject_analytics_updates:
                     subject_analytics_updates[subject.subject_name] = {"correct": 0, "attempted": 0, "time": 0, "subject_id": subject.subject_id}
                 subject_analytics_updates[subject.subject_name]["attempted"] += 1
            
            user_submission = answers_map.get(question.question_id)
            
            is_correct = False
            selected_option_ids = set()
            
            if user_submission and user_submission.selectedOptionIds:
                selected_option_ids = set(user_submission.selectedOptionIds)
                correct_option_ids = {opt.option_id for opt in question.options if opt.is_correct}
                is_correct = (correct_option_ids == selected_option_ids)

            if not user_submission or not user_submission.selectedOptionIds:
                test_answer.status = models.TestAnswerStatusEnum.UNATTEMPTED
            elif is_correct:
                final_score += question.positive_marks
                test_answer.status = models.TestAnswerStatusEnum.CORRECT
                if subject: subject_analytics_updates[subject.subject_name]["correct"] += 1
            else:
                final_score += question.negative_marks
                test_answer.status = models.TestAnswerStatusEnum.INCORRECT

        print(f"--- [DEBUG] Score Calculation Complete. Final Score: {final_score} ---")

        # 3. Update the main Test record
        test.final_score = final_score
        test.status = models.TestStatusEnum.COMPLETED
        test.end_time = datetime.now(timezone.utc)

        # 4. Update the analytics tables
        print("--- [DEBUG] Updating Analytics Tables ---")
        for subject_name, updates in subject_analytics_updates.items():
            # UPDATED: Use current_exam_id instead of hardcoded 1
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
                "user_id": current_user.user_id, 
                "exam_id": current_exam_id,  # <--- FIXED HERE
                "subject_id": updates["subject_id"],
                "attempted": updates["attempted"], 
                "correct": updates["correct"],
                "time_taken": updates["time"], 
                "now": datetime.now(timezone.utc)
            })
        print("--- [DEBUG] Analytics Update Complete ---")

        await db.commit()
        
        return {"message": "Test submitted successfully!", "testId": test_id, "finalScore": final_score, "maxScore": float(max_score)}

    except Exception as e:
        await db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")
    
@app.get("/analytics", response_model=schemas.AnalyticsResponse)
async def get_analytics_data(
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_id = current_user.user_id

    completed_tests_query = select(func.count(models.Test.test_id)).where(
        models.Test.user_id == user_id,
        models.Test.status == models.TestStatusEnum.COMPLETED
    )
    completed_tests_count_result = await db.execute(completed_tests_query)
    completed_tests_count = completed_tests_count_result.scalar_one_or_none() or 0

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

    recent_tests_query = (
        select(models.Test)
        .where(models.Test.user_id == user_id, models.Test.status == models.TestStatusEnum.COMPLETED)
        .order_by(models.Test.end_time.desc()).limit(4)
        # For recent tests, we need the subject name. 
        # Since tests are now linked to Templates, we should ideally fetch the template -> subject.
        # But for now, let's handle the 'subject' field gracefully.
        .options(selectinload(models.Test.template).selectinload(models.TestTemplate.subject))
    )
    recent_tests_results = (await db.execute(recent_tests_query)).scalars().all()
    
    recent_tests = []
    for test in recent_tests_results:
        duration_delta = test.end_time - test.start_time if test.end_time and test.start_time else timedelta(0)
        duration_mins = duration_delta.total_seconds() // 60
        
        # Fix: Access subject via the template
        subject_name = "Mixed"
        if test.template and test.template.subject:
            subject_name = test.template.subject.subject_name
        
        recent_tests.append(schemas.RecentTestData(
            name=test.test_name, 
            subject=subject_name,
            score=int(test.final_score) if test.final_score is not None else 0,
            max_score=180, 
            status=test.status.value,
            date=test.end_time.strftime("%b %d, %Y") if test.end_time else "N/A",
            time=f"{int(duration_mins)} mins"
        ))

    response_data = schemas.AnalyticsResponse(
        username=current_user.name, stats_cards=stats_cards,
        test_score_progression=test_score_progression,
        subject_performance=subject_performance,
        recent_tests=recent_tests,
    )

    print("\n--- [ANALYTICS RESPONSE DATA SENT TO FLUTTER] ---")
    print(response_data.model_dump_json(indent=2))
    print("--------------------------------------------------\n")

    return response_data

# Include the RAG router
# app.include_router(rag_routes.router)