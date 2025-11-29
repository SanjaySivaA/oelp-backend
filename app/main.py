# import re  # Add this import at the top
# from sqlalchemy import select, func  # Add func for random ordering
# from fastapi import FastAPI, Depends, HTTPException, status, Request
# from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
# from sqlalchemy.ext.asyncio import AsyncSession
# from jose import JWTError, jwt
# from passlib.context import CryptContext
# from datetime import datetime, timedelta, timezone
# import uuid
# from sqlalchemy import select
# from . import rag_routes
# from .auth import get_current_user
# from sqlalchemy.orm import selectinload # Efficiently load related options
# from sqlalchemy.orm import selectinload
# from sqlalchemy import func, case, text
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

# # project modules
# from . import models, schemas
# from .database import engine, get_db
# from .config import settings

# import json
# from typing import List, Any 

# from pathlib import Path

# from fastapi.middleware.cors import CORSMiddleware


# from fastapi.responses import JSONResponse # NEW: Import JSONResponse
# from fastapi.exceptions import RequestValidationError # NEW: Import the validation error
# import traceback
# # Use alembic

# # RAG
# from app.rag_graph import app_graph
# from .database import get_db, SessionLocal

# # --- Security & Hashing Setup ---
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# app = FastAPI()

# # --- CORS ---
# # 2. DEFINE THE ALLOWED ORIGINS (FRONTEND ADDRESSES)
# # For development, we can be permissive. Flutter web uses random ports.
# # We include the standard localhost addresses.
# origins = ["*"]
#     #"http://localhost",
#     #"http://localhost:8080",
#     # Add any other specific port your Flutter app runs on if you know it
#     # Or for maximum ease in local dev, you could use "*"
#     # "http://localhost:54321" # Example of a specific Flutter dev port
# #]


# # 3. ADD THE MIDDLEWARE TO YOUR APP
# # This should be added before your routes are defined.
# app.add_middleware(
#     CORSMiddleware,
#     #allow_origins=origins, # Allows specific origins
#     allow_origins=settings.ALLOWED_ORIGINS, # Or, allow all origins
#     allow_credentials=True,
#     allow_methods=["*"], # Allows all methods (GET, POST, etc.)
#     allow_headers=["*"], # Allows all headers
# )


# # --- Utility Functions ---

# def verify_password(plain_password, hashed_password):
#     return pwd_context.verify(plain_password, hashed_password)

# def get_password_hash(password):
#     return pwd_context.hash(password)

# def create_access_token(data: dict, expires_delta: timedelta | None = None):
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.now(timezone.utc) + expires_delta
#     else:
#         expire = datetime.now(timezone.utc) + timedelta(minutes=15)
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
#     return encoded_jwt
# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request: Request, exc: RequestValidationError):
#     print("\n--- [CRITICAL VALIDATION ERROR] ---")
#     print(f"Endpoint: {request.method} {request.url.path}")
#     # exc.errors() is a list of dictionaries explaining the validation failure
#     print(json.dumps(exc.errors(), indent=2))
#     print("-------------------------------------\n")
#     return JSONResponse(
#         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#         content={"detail": exc.errors()},
#     )
# # --- Endpoints ---

# @app.post("/register", response_model=schemas.RegisterResponse)
# async def register_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
#     # Check if user with that email already exists
#     # Note: A proper implementation would have a dedicated function for this query
#     existing_user = await db.execute(select(models.User).where(models.User.email == user.email))
#     if existing_user.scalars().first():
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Email already registered",
#         )
    
#     hashed_password = get_password_hash(user.password)
#     new_user = models.User(
#         user_id=str(uuid.uuid4()), 
#         email=user.email, 
#         name=user.name, 
#         password_hash=hashed_password
#     )
    
#     db.add(new_user)
#     await db.commit()
#     await db.refresh(new_user)
    
#     access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         data={"sub": new_user.email}, expires_delta=access_token_expires
#     )
    
#     return {
#         "user_info": new_user,
#         "token": {"access_token": access_token, "token_type": "bearer"}
#     }

# @app.get("/users/me", response_model=schemas.UserPublic)
# async def read_users_me(current_user: models.User = Depends(get_current_user)): # This line now works
#     return current_user

# @app.post("/login", response_model=schemas.Token)
# async def login_for_access_token(
#     form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
# ):
#     # Note: form_data will have 'username' and 'password' fields.
#     # We use the 'username' field for the email.
#     user_result = await db.execute(select(models.User).where(models.User.email == form_data.username))
#     user = user_result.scalars().first()
    
#     if not user or not verify_password(form_data.password, user.password_hash):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect email or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
        
#     access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         data={"sub": user.email}, expires_delta=access_token_expires
#     )
    
#     return {"access_token": access_token, "token_type": "bearer"}

# # @app.get("/getTest", response_model=schemas.TestResponse)
# # async def get_test_from_json(
# #     db: AsyncSession = Depends(get_db),
# #     current_user: models.User = Depends(get_current_user)
# # ):
# #     try:
# #         base_dir = Path(__file__).resolve().parent.parent
# #         json_file_path = base_dir / "assets" / "2017_1.json"
# #         with open(json_file_path, 'r', encoding='utf-8') as f:
# #             questions_data = json.load(f)
# #     except Exception as e:
# #         raise HTTPException(status_code=500, detail=f"Critical error reading questions file: {e}")

# #     # Create and save a new Test record in the database first.
# #     new_test = models.Test(
# #         test_id=str(uuid.uuid4()),
# #         user_id=current_user.user_id,
# #         test_name="Practice Test from JSON",
# #         test_type=models.TestTypeEnum.CUSTOM,
# #         status=models.TestStatusEnum.IN_PROGRESS,
# #         start_time=datetime.utcnow()
# #     )
# #     db.add(new_test)
# #     await db.commit()
# #     await db.refresh(new_test) # Load the new ID from the DB

# #     # Now, format the JSON questions for the frontend
# #     sections_map = {}
# #     for i, q_json in enumerate(questions_data):
# #         q_type = (q_json.get("question_type") or "UNKNOWN").strip()
# #         if q_type not in sections_map: sections_map[q_type] = []
        
# #         options = []
# #         if q_json.get("option_A"): options.append({"optionId": str(uuid.uuid4()), "optionText": q_json.get("option_A")})
# #         if q_json.get("option_B"): options.append({"optionId": str(uuid.uuid4()), "optionText": q_json.get("option_B")})
# #         if q_json.get("option_C"): options.append({"optionId": str(uuid.uuid4()), "optionText": q_json.get("option_C")})
# #         if q_json.get("option_D"): options.append({"optionId": str(uuid.uuid4()), "optionText": q_json.get("option_D")})
            
# #         sections_map[q_type].append({
# #             "questionId": f"q_{i}",
# #             "questionText": q_json.get("question_text"),
# #             "options": options,
# #             "positiveMarks": q_json.get("positive_marks"),
# #             "negativeMarks": q_json.get("negative_marks")
# #         })

# #     final_sections = [
# #         {"sectionId": f"{qt.lower()}_sec", "sectionName": f"Section - {qt}", "questionType": qt, "questions": qs}
# #         for qt, qs in sections_map.items()
# #     ]

# #     # THIS IS THE FIX: Return the REAL ID that was saved to the database.
# #     return {
# #         "sessionId": new_test.test_id,
# #         "testId": new_test.test_id,
# #         "testName": new_test.test_name,
# #         "durationInSeconds": 3600,
# #         "sections": final_sections
# #     }

# # @app.post("/tests/{test_id}/submit", response_model=schemas.TestSubmissionResponse)
# # async def submit_database_test(
# #     test_id: str,
# #     submission: schemas.TestSubmissionRequest,
# #     db: AsyncSession = Depends(get_db),
# #     current_user: models.User = Depends(get_current_user)
# # ):
# #     try:
# #         # 1. Fetch the test and all its related questions/options FROM THE DATABASE
# #         test_query = (
# #             select(models.Test)
# #             .where(models.Test.test_id == test_id, models.Test.user_id == current_user.user_id)
# #             .options(selectinload(models.Test.answers).selectinload(models.TestAnswer.question).options(selectinload(models.Question.options), selectinload(models.Question.subtopic).selectinload(models.Subtopic.chapter).selectinload(models.Chapter.subject)))
# #         )
# #         test = (await db.execute(test_query)).scalars().first()

# #         if not test: raise HTTPException(status_code=404, detail="Test session not found.")
# #         if test.status == models.TestStatusEnum.COMPLETED: raise HTTPException(status_code=400, detail="This test has already been submitted.")

# #         # 2. Score the test
# #         final_score, max_score = 0, 0
# #         answers_map = {ans.questionId: ans for ans in submission.answers}
# #         subject_analytics_updates = {}

# #         for test_answer in test.answers:
# #             question = test_answer.question
# #             max_score += question.positive_marks
            
# #             subject = question.subtopic.chapter.subject
# #             if subject.subject_name not in subject_analytics_updates:
# #                 subject_analytics_updates[subject.subject_name] = {"correct": 0, "attempted": 0, "time": 0, "subject_id": subject.subject_id}
            
# #             subject_analytics_updates[subject.subject_name]["attempted"] += 1

# #             user_submission = answers_map.get(question.question_id)
# #             if not user_submission or not user_submission.selectedOptionIds:
# #                 test_answer.status = models.TestAnswerStatusEnum.UNATTEMPTED
# #                 continue
            
# #             # THIS IS THE FIX: Compare the sets of IDs directly from the database.
# #             correct_option_ids = {opt.option_id for opt in question.options if opt.is_correct}
# #             selected_option_ids = set(user_submission.selectedOptionIds)
# #             is_correct = (correct_option_ids == selected_option_ids)
            
# #             if is_correct:
# #                 final_score += question.positive_marks
# #                 test_answer.status = models.TestAnswerStatusEnum.CORRECT
# #                 subject_analytics_updates[subject.subject_name]["correct"] += 1
# #             else:
# #                 final_score += question.negative_marks
# #                 test_answer.status = models.TestAnswerStatusEnum.INCORRECT

# #         # 3. Update the main Test record
# #         test.final_score = final_score
# #         test.status = models.TestStatusEnum.COMPLETED
# #         test.end_time = datetime.utcnow()

# #         # 4. Update the analytics tables
# #         for subject_name, updates in subject_analytics_updates.items():
# #             stmt = text(""" (Your correct analytics SQL statement) """)
# #             await db.execute(stmt, { #... (Your correct params)
# #             })
        
# #         await db.commit()
        
# #         return {"message": "Test submitted successfully!", "testId": test_id, "finalScore": final_score, "maxScore": float(max_score)}

# #     except Exception as e:
# #         await db.rollback()
# #         traceback.print_exc()
# #         raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")

# @app.get("/getTest", response_model=schemas.TestResponse)
# async def create_test_from_db(
#     db: AsyncSession = Depends(get_db),
#     current_user: models.User = Depends(get_current_user)
# ):
#     try:
#         # 1. Fetch random questions from the database WITH EAGER LOADING
#         print("[DEBUG /getTest] Fetching questions...") # Debug
#         questions_query = (
#             select(models.Question)
#             .order_by(func.random())
#             .limit(54)
#             .options(selectinload(models.Question.options)) # Eager load options
#         )
#         questions_result = await db.execute(questions_query)
#         questions = questions_result.scalars().all()
#         if not questions:
#             raise HTTPException(status_code=404, detail="No questions found in database.")
#         print(f"[DEBUG /getTest] Fetched {len(questions)} questions.") # Debug

#         # 2. IMMEDIATELY Format the response data WHILE THE SESSION IS ACTIVE
#         # This prevents the MissingGreenlet error by accessing attributes now.
#         print("[DEBUG /getTest] Formatting response sections...") # Debug
#         sections_map = {}
#         for q in questions:
#             # Access attributes needed for the response *now*
#             q_type = q.question_type.value if q.question_type else "UNKNOWN"
#             question_id = q.question_id
#             question_text = q.question_text
#             positive_marks = q.positive_marks
#             negative_marks = q.negative_marks
#             options_list = [{"optionId": opt.option_id, "optionText": opt.option_text} for opt in q.options]

#             if q_type not in sections_map: sections_map[q_type] = []
#             sections_map[q_type].append({
#                 "questionId": question_id, "questionText": question_text,
#                 "options": options_list,
#                 "positiveMarks": positive_marks, "negativeMarks": negative_marks
#             })
        
#         final_sections = [
#             {"sectionId": f"{qt.lower()}_sec", "sectionName": f"Section - {qt}", "questionType": qt, "questions": qs}
#             for qt, qs in sections_map.items()
#         ]
#         print("[DEBUG /getTest] Response sections formatted.") # Debug

#         # 3. Create and save the new Test session record
#         print("[DEBUG /getTest] Creating Test record in DB...") # Debug
#         new_test = models.Test(
#             test_id=str(uuid.uuid4()), user_id=current_user.user_id,
#             test_name="Dynamic Practice Test", test_type=models.TestTypeEnum.CUSTOM,
#             status=models.TestStatusEnum.IN_PROGRESS, start_time=datetime.utcnow()
#         )
#         db.add(new_test)
        
#         # 4. Create the placeholder TestAnswer records
#         # We use the question objects directly fetched earlier
#         print("[DEBUG /getTest] Creating placeholder TestAnswer records...") # Debug
#         answers_to_add = [
#             models.TestAnswer(answer_id=str(uuid.uuid4()), test=new_test, question=question)
#             for question in questions
#         ]
#         db.add_all(answers_to_add)
        
#         print("[DEBUG /getTest] Committing Test and TestAnswers...") # Debug
#         await db.commit()
#         await db.refresh(new_test) # Refresh to ensure ID is loaded
#         print("[DEBUG /getTest] Commit successful.") # Debug

#         # 5. Return the formatted data
#         return {
#             "sessionId": new_test.test_id, "testId": new_test.test_id,
#             "testName": new_test.test_name, "durationInSeconds": 3600,
#             "sections": final_sections
#         }
#     except Exception as e:
#         # Provide more context in case of error
#         print("\n--- ERROR IN /getTest ---")
#         traceback.print_exc()
#         print("-------------------------\n")
#         # Ensure rollback occurs if commit failed
#         await db.rollback()
#         raise HTTPException(status_code=500, detail=f"Error creating test: {e}")

# @app.post("/tests/{test_id}/submit", response_model=schemas.TestSubmissionResponse)
# async def submit_database_test(
#     test_id: str,
#     submission: schemas.TestSubmissionRequest,
#     db: AsyncSession = Depends(get_db),
#     current_user: models.User = Depends(get_current_user)
# ):
#     try:
#         # 1. Fetch the test and all its related data FROM THE DATABASE
#         test_query = (
#             select(models.Test)
#             .where(models.Test.test_id == test_id, models.Test.user_id == current_user.user_id)
#             .options(
#                 # Eager load everything needed for scoring and analytics
#                 selectinload(models.Test.answers)
#                 .selectinload(models.TestAnswer.question)
#                 .options(
#                     selectinload(models.Question.options), # Need options for correct answer check
#                     selectinload(models.Question.subtopic) # Need subtopic -> chapter -> subject for analytics
#                     .selectinload(models.Subtopic.chapter)
#                     .selectinload(models.Chapter.subject)
#                 )
#             )
#         )
#         test = (await db.execute(test_query)).scalars().first()

#         if not test: raise HTTPException(status_code=404, detail="Test session not found.")
#         if test.status == models.TestStatusEnum.COMPLETED: raise HTTPException(status_code=400, detail="This test has already been submitted.")

#         # 2. Score the test
#         final_score, max_score = 0, 0
#         answers_map = {ans.questionId: ans for ans in submission.answers}
#         subject_analytics_updates = {}

#         print("\n--- [DEBUG] Starting Score Calculation ---") # DEBUG
#         for test_answer in test.answers:
#             question = test_answer.question
#             if not question: # Safety check
#                 print(f"  [WARN] Skipping TestAnswer {test_answer.answer_id} due to missing Question link.")
#                 continue
                
#             max_score += question.positive_marks
            
#             # Safely get subject info
#             subject = None
#             if question.subtopic and question.subtopic.chapter and question.subtopic.chapter.subject:
#                  subject = question.subtopic.chapter.subject
#                  if subject.subject_name not in subject_analytics_updates:
#                      subject_analytics_updates[subject.subject_name] = {"correct": 0, "attempted": 0, "time": 0, "subject_id": subject.subject_id}
#                  subject_analytics_updates[subject.subject_name]["attempted"] += 1
#             else:
#                  print(f"  [WARN] Cannot find subject for Question {question.question_id}. Skipping analytics update for this question.")


#             user_submission = answers_map.get(question.question_id)
            
#             # --- Evaluation Logic ---
#             is_correct = False # Default to incorrect
#             selected_option_ids = set()
            
#             if user_submission and user_submission.selectedOptionIds:
#                 selected_option_ids = set(user_submission.selectedOptionIds)
                
#                 # Get correct IDs directly from the database objects
#                 correct_option_ids = {opt.option_id for opt in question.options if opt.is_correct}
                
#                 # =======================================================================
#                 # THIS IS THE FIX: The comparison logic is now correct.
#                 # =======================================================================
#                 is_correct = (correct_option_ids == selected_option_ids)

#                 print(f"  Q: {question.question_id[:8]}...") # DEBUG
#                 print(f"    Correct IDs : {sorted(list(correct_option_ids))}") # DEBUG
#                 print(f"    Selected IDs: {sorted(list(selected_option_ids))}") # DEBUG
#                 print(f"    Result      : {'CORRECT' if is_correct else 'INCORRECT'}") # DEBUG
            
#             # --- Update Score and Status ---
#             if not user_submission or not user_submission.selectedOptionIds:
#                 test_answer.status = models.TestAnswerStatusEnum.UNATTEMPTED
#                 print(f"  Q: {question.question_id[:8]}... Unattempted") # DEBUG
#             elif is_correct:
#                 final_score += question.positive_marks
#                 test_answer.status = models.TestAnswerStatusEnum.CORRECT
#                 if subject: subject_analytics_updates[subject.subject_name]["correct"] += 1
#             else:
#                 final_score += question.negative_marks
#                 test_answer.status = models.TestAnswerStatusEnum.INCORRECT

#         print(f"--- [DEBUG] Score Calculation Complete. Final Score: {final_score} ---") # DEBUG

#         # 3. Update the main Test record
#         test.final_score = final_score
#         test.status = models.TestStatusEnum.COMPLETED
#         test.end_time = datetime.utcnow()

#         # 4. Update the analytics tables
#         print("--- [DEBUG] Updating Analytics Tables ---") # DEBUG
#         for subject_name, updates in subject_analytics_updates.items():
#             print(f"  Updating analytics for {subject_name}: Attempted={updates['attempted']}, Correct={updates['correct']}") # DEBUG
#             stmt = text("""
#                 INSERT INTO user_subject_analytics (user_id, exam_id, subject_id, questions_attempted, correct_answers, total_time_taken_seconds, last_updated_at)
#                 VALUES (:user_id, :exam_id, :subject_id, :attempted, :correct, :time_taken, :now)
#                 ON CONFLICT (user_id, exam_id, subject_id) DO UPDATE SET
#                 questions_attempted = user_subject_analytics.questions_attempted + :attempted,
#                 correct_answers = user_subject_analytics.correct_answers + :correct,
#                 total_time_taken_seconds = user_subject_analytics.total_time_taken_seconds + :time_taken,
#                 last_updated_at = :now;
#             """)
#             await db.execute(stmt, {
#                 "user_id": current_user.user_id, "exam_id": 1, "subject_id": updates["subject_id"],
#                 "attempted": updates["attempted"], "correct": updates["correct"],
#                 "time_taken": updates["time"], "now": datetime.utcnow()
#             })
#         print("--- [DEBUG] Analytics Update Complete ---") # DEBUG

#         print("--- [DEBUG] Committing Transaction ---") # DEBUG
#         await db.commit()
#         print("--- [DEBUG] Commit Successful ---") # DEBUG
        
#         return {"message": "Test submitted successfully!", "testId": test_id, "finalScore": final_score, "maxScore": float(max_score)}

#     except Exception as e:
#         # Ensure rollback happens on any error
#         await db.rollback()
#         traceback.print_exc() # Print full error for debugging
#         raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")
    
# @app.get("/analytics", response_model=schemas.AnalyticsResponse)
# async def get_analytics_data(
#     current_user: models.User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ):
#     user_id = current_user.user_id

#     # --- Query 1: Stats Cards ---
#     completed_tests_query = select(func.count(models.Test.test_id)).where(
#         models.Test.user_id == user_id,
#         models.Test.status == models.TestStatusEnum.COMPLETED
#     )
#     completed_tests_count_result = await db.execute(completed_tests_query)
#     completed_tests_count = completed_tests_count_result.scalar_one_or_none() or 0

#     # --- Query 2: Average Accuracy ---
#     accuracy_query = select(
#         func.sum(models.UserSubjectAnalytics.correct_answers),
#         func.sum(models.UserSubjectAnalytics.questions_attempted)
#     ).where(models.UserSubjectAnalytics.user_id == user_id)
#     accuracy_result = await db.execute(accuracy_query)
#     total_correct, total_attempted = accuracy_result.first() or (0, 0)
#     average_accuracy = (total_correct / total_attempted * 100) if total_attempted else 0.0

#     stats_cards = [
#         schemas.StatsCardData(title="Total Tests Completed", value=str(completed_tests_count), change="", trend_color="green"),
#         schemas.StatsCardData(title="Average Accuracy", value=f"{average_accuracy:.1f}%", change="", trend_color="green"),
#     ]

#     # --- Query 3: Score Progression ---
#     score_progression_query = (
#         select(models.Test.final_score, models.Test.end_time)
#         .where(models.Test.user_id == user_id, models.Test.status == models.TestStatusEnum.COMPLETED, models.Test.final_score.is_not(None))
#         .order_by(models.Test.end_time.asc()).limit(7)
#     )
#     score_results = (await db.execute(score_progression_query)).all()
#     test_score_progression = schemas.TestScoreProgressionData(
#         spots=[schemas.ChartSpot(x=float(i), y=score) for i, (score, _) in enumerate(score_results)],
#         dates=[dt.strftime("%b %d") for _, dt in score_results]
#     )

#     # --- Query 4: Subject Performance ---
#     subject_perf_query = (
#         select(models.Subject.subject_name, models.UserSubjectAnalytics.correct_answers, models.UserSubjectAnalytics.questions_attempted)
#         .join(models.Subject, models.UserSubjectAnalytics.subject_id == models.Subject.subject_id)
#         .where(models.UserSubjectAnalytics.user_id == user_id)
#     )
#     subject_perf_results = (await db.execute(subject_perf_query)).all()
#     subject_performance = [
#         schemas.SubjectPerformanceData(subject_name=name, accuracy=(correct / attempted * 100) if attempted else 0)
#         for name, correct, attempted in subject_perf_results
#     ]

#     # --- Query 5: Recent Tests ---
#     recent_tests_query = (
#         select(models.Test)
#         .where(models.Test.user_id == user_id, models.Test.status == models.TestStatusEnum.COMPLETED)
#         .order_by(models.Test.end_time.desc()).limit(4)
#         .options(selectinload(models.Test.subject))
#     )
#     recent_tests_results = (await db.execute(recent_tests_query)).scalars().all()
    
#     recent_tests = []
#     for test in recent_tests_results:
#         duration_delta = test.end_time - test.start_time if test.end_time and test.start_time else timedelta(0)
#         duration_mins = duration_delta.total_seconds() // 60
        
#         recent_tests.append(schemas.RecentTestData(
#             name=test.test_name, subject=test.subject.subject_name if test.subject else "Mixed",
#             score=int(test.final_score) if test.final_score is not None else 0,
#             max_score=180, # Placeholder
#             status=test.status.value,
#             date=test.end_time.strftime("%b %d, %Y") if test.end_time else "N/A",
#             time=f"{int(duration_mins)} mins"
#         ))

#     # Construct the final response object
#     response_data = schemas.AnalyticsResponse(
#         username=current_user.name, stats_cards=stats_cards,
#         test_score_progression=test_score_progression,
#         subject_performance=subject_performance,
#         recent_tests=recent_tests,
#     )

#     # =======================================================================
#     # THE BLACK BOX RECORDER: This will print the exact data being sent.
#     # =======================================================================
#     print("\n--- [ANALYTICS RESPONSE DATA SENT TO FLUTTER] ---")
#     # We use model_dump_json for a clean, indented print of the Pydantic model
#     print(response_data.model_dump_json(indent=2))
#     print("--------------------------------------------------\n")

#     return response_data

# # =======================================================================
# # NEW: QUESTIONS ENDPOINT
# # =======================================================================
# @app.get("/questions", response_model=List[Any])
# async def get_questions(current_user: models.User = Depends(get_current_user)):
#     """
#     Reads the questions from a JSON file and returns them.
#     This endpoint is protected and requires user authentication.
#     """
#     try:
#         # The path is relative to where you run uvicorn (the oelp-backend folder)
#         with open('assets/2017_1.json', 'r', encoding='utf-8') as f:
#             data = json.load(f)
#         return data
#     except FileNotFoundError:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, 
#             detail="Questions file not found on the server."
#         )
#     except json.JSONDecodeError:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Error decoding the questions JSON file."
#         )

# # =======================================================================
# # NEW: TEST SUBMISSION AND EVALUATION ENDPOINT
# # =======================================================================
# @app.post("/tests/submit", response_model=schemas.TestSubmissionResponse)
# async def submit_json_test(
#     submission: schemas.TestSubmissionRequest,
#     db: AsyncSession = Depends(get_db),
#     current_user: models.User = Depends(get_current_user)
# ):
#     try:
#         base_dir = Path(__file__).resolve().parent.parent
#         json_file_path = base_dir / "assets" / "2017_1.json"
#         with open(json_file_path, 'r', encoding='utf-8') as f:
#             questions_data = json.load(f)
        
#         final_score, max_score = 0, sum(q.get("positive_marks", 0) for q in questions_data)
#         answers_map = {ans.questionId: ans for ans in submission.answers}

#         for i, question_details in enumerate(questions_data):
#             question_id = f"q_{i}"
#             user_submission = answers_map.get(question_id)

#             if not user_submission or not user_submission.selectedOptionIds:
#                 continue
            
#             correct_option_str = question_details.get("correct_option")
#             correct_option_texts = set()
#             if correct_option_str:
#                 correct_letters = [letter.strip() for letter in correct_option_str.split(',')]
#                 correct_option_texts = {question_details.get(f"option_{l}") for l in correct_letters if question_details.get(f"option_{l}")}

#             selected_option_texts = set(user_submission.selectedOptionIds)

#             if correct_option_texts == selected_option_texts:
#                 final_score += question_details.get("positive_marks", 0)
#             else:
#                 final_score += question_details.get("negative_marks", 0)
        
#         completed_test = models.Test(
#             test_id=submission.sessionId, user_id=current_user.user_id,
#             test_name="Practice Test from JSON", test_type=models.TestTypeEnum.CUSTOM,
#             status=models.TestStatusEnum.COMPLETED,
#             start_time=datetime.utcnow() - timedelta(minutes=60),
#             end_time=datetime.utcnow(), final_score=final_score
#         )
#         db.add(completed_test)
#         await db.commit()
        
#         return {"message": "Test submitted successfully!", "testId": submission.sessionId, "finalScore": final_score, "maxScore": float(max_score)}

#     except Exception as e:
#         await db.rollback()
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")

# # =======================================================================
# # UPDATED RAG TASK (Uses LangGraph)
# # =======================================================================
# async def generate_remedial_questions_task(wrong_questions_data: List[dict]):
#     """
#     Runs the Self-Correcting LangGraph Agent in the background.
#     """
#     print(f"--- [RAG AGENT] Started processing {len(wrong_questions_data)} wrong answers... ---")
    
#     # FIX: Use the existing SessionLocal factory from database.py
#     # This reuses the connection pool instead of creating a new one.
#     async with SessionLocal() as db:
#         for q_data in wrong_questions_data:
#             original_text = q_data['text']
#             subject_name = q_data['subject']
            
#             # --- INVOKE THE GRAPH ---
#             initial_state = {
#                 "original_question": original_text,
#                 "subject": subject_name,
#                 "attempts": 0
#             }
            
#             final_state = await app_graph.ainvoke(initial_state)
            
#             new_q_json = final_state.get("generated_question_json")
#             feedback = final_state.get("feedback")

#             if new_q_json and feedback == "valid":
#                 # ... (Logic to save new question is exactly the same as before) ...
#                 new_id = str(uuid.uuid4())
#                 new_question = models.Question(
#                     question_id=new_id,
#                     question_text=new_q_json['question_text'],
#                     question_type=models.QuestionType.MCSC,
#                     difficulty_level=models.DifficultyLevel.MEDIUM,
#                     source=models.SourceEnum.GENERATED,
#                     positive_marks=4, negative_marks=1,
#                     solution_explanation=new_q_json.get('solution_explanation'),
#                     subtopic_id=None 
#                 )
#                 db.add(new_question)
#                 await db.flush()

#                 for letter in ['A', 'B', 'C', 'D']:
#                     opt_text = new_q_json.get(f"option_{letter}")
#                     if opt_text:
#                         db.add(models.QuestionOption(
#                             option_id=str(uuid.uuid4()),
#                             question_id=new_id,
#                             option_text=opt_text,
#                             is_correct=(letter == new_q_json.get('correct_option'))
#                         ))
                
#                 print(f"--- [RAG AGENT] Graph Successfully Generated & Validated: {new_id} ---")
#             else:
#                 print(f"--- [RAG AGENT] Failed to generate valid question. ---")

#         await db.commit()


import json
import traceback
import uuid
from typing import List, Any
from pathlib import Path
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, text
from passlib.context import CryptContext
from jose import jwt

# Project modules
from . import models, schemas
from .database import get_db, SessionLocal 
from .config import settings
from .auth import get_current_user

# RAG Imports
from app.rag_graph import app_graph

# --- Setup ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Auth Functions ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=1))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"\n--- [VALIDATION ERROR] {request.url.path} ---\n{json.dumps(exc.errors(), indent=2)}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

# --- Auth Endpoints ---
@app.post("/register", response_model=schemas.RegisterResponse)
async def register_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(models.User).where(models.User.email == user.email))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = models.User(
        user_id=str(uuid.uuid4()), email=user.email, name=user.name, 
        password_hash=get_password_hash(user.password), created_at=datetime.utcnow()
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    token = create_access_token(data={"sub": new_user.email})
    return {"user_info": new_user, "token": {"access_token": token, "token_type": "bearer"}}

@app.post("/login", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(models.User).where(models.User.email == form_data.username))).scalars().first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return {"access_token": create_access_token(data={"sub": user.email}), "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.UserPublic)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# =======================================================================
# BACKGROUND TASK: RAG AGENT
# =======================================================================
async def generate_remedial_questions_task(wrong_questions_data: List[dict]):
    """
    1. Analyzes wrong questions.
    2. Generates new ones using LangGraph.
    3. PRINTS JSON TO TERMINAL.
    4. Saves to DB.
    """
    print(f"\n\n{'='*60}")
    print(f"🚀 [RAG AGENT ACTIVATED] Processing {len(wrong_questions_data)} mistakes")
    print(f"{'='*60}\n")
    
    async with SessionLocal() as db:
        for i, q_data in enumerate(wrong_questions_data):
            original_text = q_data['text']
            # If subject is None/Empty in DB, we pass "Unknown" so Agent figures it out
            subject_hint = q_data['subject'] if q_data['subject'] else "Unknown"
            
            print(f"--- Processing Question {i+1} ---")
            print(f"📝 Original Q: {original_text[:100]}...")
            print(f"🔍 Database Subject: {subject_hint}")

            # --- 1. Invoke Graph ---
            initial_state = {
                "original_question": original_text,
                "subject": subject_hint,
                "attempts": 0
            }
            
            try:
                final_state = await app_graph.ainvoke(initial_state)
                new_q_json = final_state.get("generated_question_json")
                feedback = final_state.get("feedback")

                if new_q_json and feedback == "valid":
                    # --- 2. PRINT TO TERMINAL (Your Request) ---
                    print(f"\n✨ [GENERATION SUCCESS]")
                    print(f"🧠 AI Detected Concept: {new_q_json.get('detected_concept', 'N/A')}")
                    print(f"📄 Generated JSON:")
                    print(json.dumps(new_q_json, indent=2)) # Pretty print JSON
                    print("-" * 40)

                    # --- 3. Save to Database ---
                    # Logic: If we couldn't find a subtopic originally, we default to ID 1
                    # (In a real app, you might try to match 'detected_concept' to a DB Subtopic)
                    subtopic_id = q_data.get('subtopic_id') or 1 

                    new_id = str(uuid.uuid4())
                    new_question = models.Question(
                        question_id=new_id,
                        question_text=new_q_json['question_text'],
                        question_type=models.QuestionTypeEnum.MCSC,
                        difficulty_level=models.DifficultyLevelEnum.MEDIUM,
                        source=models.SourceEnum.GENERATED,
                        positive_marks=4, negative_marks=1,
                        solution_explanation=new_q_json.get('solution_explanation'),
                        subtopic_id=subtopic_id 
                    )
                    db.add(new_question)
                    await db.flush()

                    for letter in ['A', 'B', 'C', 'D']:
                        opt_text = new_q_json.get(f"option_{letter}")
                        if opt_text:
                            db.add(models.QuestionOption(
                                option_id=str(uuid.uuid4()),
                                question_id=new_id,
                                option_text=opt_text,
                                is_correct=(letter == new_q_json.get('correct_option'))
                            ))
                else:
                    print(f"❌ [GENERATION FAILED] Feedback: {feedback}")

            except Exception as e:
                print(f"❌ [CRITICAL GRAPH ERROR] {e}")

        await db.commit()
        print(f"\n{'='*60}")
        print("✅ [RAG CYCLE COMPLETE] All questions processed.")
        print(f"{'='*60}\n")

# =======================================================================
# 1. /getTest (Database Driven - FIX APPLIED)
# =======================================================================
@app.get("/getTest", response_model=schemas.TestResponse)
async def create_test_from_db(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 1. Fetch random questions
    questions_query = (
        select(models.Question)
        .order_by(func.random())
        .limit(54)
        .options(selectinload(models.Question.options))
    )
    questions = (await db.execute(questions_query)).scalars().all()
    
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found in database.")

    # --- FIX STARTS HERE: Create a Template First ---
    # We need a template ID to create a test. 
    # Since this is a random custom test, we create a placeholder template.
    template_id = str(uuid.uuid4())
    new_template = models.TestTemplate(
        template_id=template_id,
        owner_user_id=current_user.user_id,
        exam_id=1, # Default to Exam ID 1 (JEE Main)
        template_name="Dynamic Practice Template",
        test_type=models.TestTypeEnum.CUSTOM,
        duration_minutes=60,
        created_at=datetime.utcnow()
    )
    db.add(new_template)
    await db.flush() # Save to DB to generate the ID usable by Test
    # --- FIX ENDS HERE ---

    # 2. Create Test Record LINKED to the Template
    new_test = models.Test(
        test_id=str(uuid.uuid4()), 
        user_id=current_user.user_id,
        template_id=template_id, # <--- Added this Link
        test_name="Dynamic Practice Test", 
        test_type=models.TestTypeEnum.CUSTOM,
        status=models.TestStatusEnum.IN_PROGRESS, 
        start_time=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    db.add(new_test)
    
    # 3. Create TestAnswers
    sections_map = {}
    
    for q in questions:
        db.add(models.TestAnswer(answer_id=str(uuid.uuid4()), test=new_test, question=q))
        
        q_type = q.question_type.value if q.question_type else "UNKNOWN"
        if q_type not in sections_map: sections_map[q_type] = []
        
        sections_map[q_type].append({
            "questionId": q.question_id, "questionText": q.question_text,
            "options": [{"optionId": opt.option_id, "optionText": opt.option_text} for opt in q.options],
            "positiveMarks": q.positive_marks, "negativeMarks": q.negative_marks
        })

    await db.commit()
    await db.refresh(new_test)

    final_sections = [
        {"sectionId": f"{qt.lower()}_sec", "sectionName": f"Section - {qt}", "questionType": qt, "questions": qs}
        for qt, qs in sections_map.items()
    ]

    return {
        "sessionId": new_test.test_id, "testId": new_test.test_id,
        "testName": new_test.test_name, 
        "durationInSeconds": 60, # Keep this 60 for your testing
        "sections": final_sections
    }

# Add this helper function in app/main.py (before the submit endpoint)

def calculate_score_logic(question, user_selected_ids: set):
    """
    Calculates score based on JEE Advanced Partial Marking Logic.
    """
    correct_option_ids = {opt.option_id for opt in question.options if opt.is_correct}
    
    # 1. UNATTEMPTED
    if not user_selected_ids:
        return 0, models.TestAnswerStatusEnum.UNATTEMPTED

    # 2. INCORRECT (Negative Marking)
    # Rule: If ANY selected option is NOT in the correct set, it's immediately wrong.
    # Logic: If selected_ids is NOT a subset of correct_ids
    if not user_selected_ids.issubset(correct_option_ids):
        # Return negative marks (e.g., -1 for MCSC, -2 for MCMC)
        return -1 * question.negative_marks, models.TestAnswerStatusEnum.INCORRECT

    # 3. FULLY CORRECT
    if user_selected_ids == correct_option_ids:
        return question.positive_marks, models.TestAnswerStatusEnum.CORRECT

    # 4. PARTIAL MARKING (Only for MCMC / MCMC)
    # At this point, we know user_selected_ids is a SUBSET of correct_ids.
    if question.question_type == models.QuestionTypeEnum.MCMC: # Use Enum!
        n_correct_total = len(correct_option_ids)
        n_selected = len(user_selected_ids)
        
        score = 0
        
        # JEE Advanced Partial Rules (2018-2024 patterns)
        if n_correct_total >= 4 and n_selected == 3:
            score = 3
        elif n_correct_total >= 3 and n_selected == 2:
            score = 2
        elif n_correct_total >= 2 and n_selected == 1:
            score = 1
        else:
            # Fallback for edge cases (e.g. 1 correct option in MCMC acts like MCSC)
            score = 1 if n_selected == 1 else 0

        if score > 0:
            return score, models.TestAnswerStatusEnum.CORRECT # Or PARTIALLY_CORRECT if you add that enum
    
    # If it's MCSC (Single Correct) but they selected a subset (impossible for size 1), 
    # or some other edge case, give 0 or negative.
    return 0, models.TestAnswerStatusEnum.INCORRECT

# =======================================================================
# 2. /submit (Database Driven + RAG Trigger)
# =======================================================================
@app.post("/tests/{test_id}/submit", response_model=schemas.TestSubmissionResponse)
async def submit_database_test(
    test_id: str,
    submission: schemas.TestSubmissionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 1. Fetch Test & Questions
    test_query = (
        select(models.Test)
        .where(models.Test.test_id == test_id, models.Test.user_id == current_user.user_id)
        .options(
            selectinload(models.Test.answers)
            .selectinload(models.TestAnswer.question)
            .options(
                selectinload(models.Question.options),
                selectinload(models.Question.subtopic).selectinload(models.Subtopic.chapter).selectinload(models.Chapter.subject)
            )
        )
    )
    test = (await db.execute(test_query)).scalars().first()
    if not test: raise HTTPException(status_code=404, detail="Test session not found.")
    if test.status == models.TestStatusEnum.COMPLETED: raise HTTPException(status_code=400, detail="Test already submitted.")

    final_score = 0
    max_score = 0
    answers_map = {ans.questionId: ans for ans in submission.answers}
    subject_analytics = {}
    wrong_questions_for_rag = []

    # 2. Iterate through every question in the test
    for test_answer in test.answers:
        q = test_answer.question
        if not q: continue
        
        max_score += q.positive_marks
        
        # Get User's Submission for this question
        user_sub = answers_map.get(q.question_id)
        
        # --- A. SAVE USER RESPONSES TO DATABASE ---
        if user_sub:
            # CASE 1: MCSC & MCMC (Save to test_answer_selections table)
            if q.question_type in [models.QuestionTypeEnum.MCSC, models.QuestionTypeEnum.MCMC]:
                if user_sub.selectedOptionIds:
                    for opt_id in user_sub.selectedOptionIds:
                        # Create the link between the Answer and the Selected Option
                        new_selection = models.TestAnswerSelection(
                            answer_id=test_answer.answer_id,
                            selected_option_id=opt_id
                        )
                        db.add(new_selection)

            # CASE 2: NUMERICAL (Save to integer_answer column)
            elif q.question_type == models.QuestionTypeEnum.NUMERICAL:
                if user_sub.integerAnswer is not None:
                    test_answer.integer_answer = user_sub.integerAnswer

        # --- B. ANALYTICS SETUP ---
        subj_name = "General"
        subj_id = 1
        subtopic_id = 1
        
        if q.subtopic:
            subtopic_id = q.subtopic.subtopic_id
            if q.subtopic.chapter and q.subtopic.chapter.subject:
                subj_name = q.subtopic.chapter.subject.subject_name
                subj_id = q.subtopic.chapter.subject.subject_id
        
        if subj_name not in subject_analytics:
            subject_analytics[subj_name] = {"correct": 0, "attempted": 0, "time": 0, "id": subj_id}
        
        if user_sub and (user_sub.selectedOptionIds or user_sub.integerAnswer is not None):
            subject_analytics[subj_name]["attempted"] += 1

        # --- C. SCORING LOGIC ---
        score = 0
        status = models.TestAnswerStatusEnum.UNATTEMPTED

        # Logic for MCSC / MCMC
        if q.question_type in [models.QuestionTypeEnum.MCSC, models.QuestionTypeEnum.MCMC]:
            selected_ids = set(user_sub.selectedOptionIds) if (user_sub and user_sub.selectedOptionIds) else set()
            score, status = calculate_score_logic(q, selected_ids)
        
        # Logic for NUMERICAL
        elif q.question_type == models.QuestionTypeEnum.NUMERICAL:
            user_val = user_sub.integerAnswer if user_sub else None
            if user_val is not None:
                # NOTE: This assumes you store the correct numerical answer 
                # inside the 'solution_explanation' or a specific column.
                # For now, we assume if it matches the first option's text (common hack) or you add a column later.
                # This is a placeholder for numerical matching:
                correct_val = extract_correct_numerical_value(q) 
                if correct_val is not None and user_val == correct_val:
                    score = q.positive_marks
                    status = models.TestAnswerStatusEnum.CORRECT
                else:
                    score = 0 # No negative marking usually for numerical, or -1
                    status = models.TestAnswerStatusEnum.INCORRECT
            else:
                status = models.TestAnswerStatusEnum.UNATTEMPTED

        # Update Totals
        final_score += score
        test_answer.status = status
        
        # Update Analytics & RAG Trigger
        if status == models.TestAnswerStatusEnum.CORRECT:
            subject_analytics[subj_name]["correct"] += 1
        elif status == models.TestAnswerStatusEnum.INCORRECT:
             wrong_questions_for_rag.append({
                 "text": q.question_text,
                 "subject": subj_name if subj_name != "General" else None, 
                 "subtopic_id": subtopic_id
             })

    # 3. Finalize Test Record
    test.final_score = final_score
    test.status = models.TestStatusEnum.COMPLETED
    test.end_time = datetime.utcnow()

    # 4. Save Analytics
    for s_name, data in subject_analytics.items():
        stmt = text("""
            INSERT INTO user_subject_analytics (user_id, exam_id, subject_id, questions_attempted, correct_answers, total_time_taken_seconds, last_updated_at)
            VALUES (:uid, :eid, :sid, :att, :corr, :time, :now)
            ON CONFLICT (user_id, exam_id, subject_id) DO UPDATE SET
            questions_attempted = user_subject_analytics.questions_attempted + :att,
            correct_answers = user_subject_analytics.correct_answers + :corr,
            last_updated_at = :now;
        """)
        await db.execute(stmt, {
            "uid": current_user.user_id, "eid": 1, "sid": data["id"],
            "att": data["attempted"], "corr": data["correct"], "time": 0, "now": datetime.utcnow()
        })

    await db.commit()

    # 5. Trigger RAG Agent
    if wrong_questions_for_rag:
        background_tasks.add_task(generate_remedial_questions_task, wrong_questions_for_rag)

    return {
        "message": "Test submitted!",
        "testId": test_id,
        "finalScore": final_score,
        "maxScore": float(max_score)
    }

# Helper to safely extract numerical answer (You might need to adjust based on how you seed data)
def extract_correct_numerical_value(question) -> int | None:
    # If you store the answer in the first option text as a string "5":
    try:
        if question.options:
            for opt in question.options:
                if opt.is_correct:
                    return int(float(opt.option_text)) # Handle "5.0" or "5"
    except:
        return None
    return None

# =======================================================================
# 3. /analytics (Database Driven)
# =======================================================================
@app.get("/analytics", response_model=schemas.AnalyticsResponse)
async def get_analytics_data(
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_id = current_user.user_id

    # 1. Completed Tests Count
    completed = (await db.execute(
        select(func.count(models.Test.test_id))
        .where(models.Test.user_id == user_id, models.Test.status == models.TestStatusEnum.COMPLETED)
    )).scalar_one()

    # 2. Accuracy
    acc_res = (await db.execute(
        select(func.sum(models.UserSubjectAnalytics.correct_answers), func.sum(models.UserSubjectAnalytics.questions_attempted))
        .where(models.UserSubjectAnalytics.user_id == user_id)
    )).first()
    total_corr, total_att = acc_res or (0, 0)
    avg_acc = (total_corr / total_att * 100) if total_att else 0.0

    stats = [
        schemas.StatsCardData(title="Tests Completed", value=str(completed), change="", trend_color="green"),
        schemas.StatsCardData(title="Avg Accuracy", value=f"{avg_acc:.1f}%", change="", trend_color="green"),
    ]

    # 3. Score Progression
    scores = (await db.execute(
        select(models.Test.final_score, models.Test.end_time)
        .where(models.Test.user_id == user_id, models.Test.status == models.TestStatusEnum.COMPLETED)
        .order_by(models.Test.end_time.asc()).limit(7)
    )).all()
    
    progression = schemas.TestScoreProgressionData(
        spots=[schemas.ChartSpot(x=float(i), y=s[0]) for i, s in enumerate(scores)],
        dates=[s[1].strftime("%b %d") for s in scores]
    )

    # 4. Subject Performance
    sub_perf = (await db.execute(
        select(models.Subject.subject_name, models.UserSubjectAnalytics.correct_answers, models.UserSubjectAnalytics.questions_attempted)
        .join(models.Subject)
        .where(models.UserSubjectAnalytics.user_id == user_id)
    )).all()
    perf_list = [schemas.SubjectPerformanceData(subject_name=r[0], accuracy=(r[1]/r[2]*100) if r[2] else 0) for r in sub_perf]

    # --- FIX STARTS HERE (Recent Tests) ---
    recent = (await db.execute(
        select(models.Test)
        .where(models.Test.user_id == user_id, models.Test.status == models.TestStatusEnum.COMPLETED)
        .order_by(models.Test.end_time.desc())
        .limit(5)
        # UPDATED: Load Template -> Subject instead of just Subject
        .options(selectinload(models.Test.template).selectinload(models.TestTemplate.subject))
    )).scalars().all()
    
    recent_list = []
    for t in recent:
        # Time Calculation
        if t.start_time and t.end_time:
            duration = t.end_time - t.start_time
            minutes = int(duration.total_seconds() // 60)
            if minutes < 1:
                time_str = f"{int(duration.total_seconds())}s"
            else:
                time_str = f"{minutes}m"
        else:
            time_str = "N/A"

        # UPDATED: Safety check for Template and Subject
        subj_name = "Mixed"
        if t.template and t.template.subject:
            subj_name = t.template.subject.subject_name
        
        recent_list.append(
            schemas.RecentTestData(
                test_id=t.test_id,
                name=t.test_name, 
                subject=subj_name, 
                score=int(t.final_score) if t.final_score is not None else 0, 
                max_score=180, 
                status=t.status.value,
                date=t.end_time.strftime("%b %d") if t.end_time else "", 
                time=time_str
            )
        )
    # --- FIX ENDS HERE ---

    return schemas.AnalyticsResponse(
        username=current_user.name, stats_cards=stats, test_score_progression=progression,
        subject_performance=perf_list, recent_tests=recent_list
    )

# =======================================================================
# 1. LIST CHAPTERS (Populates the Selection Screen)
# =======================================================================
@app.get("/subjects/{subject_name}/chapters", response_model=List[schemas.ChapterCard])
async def get_chapters_for_subject(
    subject_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    print(f"--- Fetching Chapters for {subject_name} ---")
    
    # Logic: Get all chapters linked to this Subject Name
    query = (
        select(models.Chapter)
        .join(models.Subject)
        .where(models.Subject.subject_name.ilike(subject_name)) # ilike for case-insensitive (Physics/physics)
        .order_by(models.Chapter.chapter_name)
    )
    
    result = await db.execute(query)
    chapters = result.scalars().all()
    
    response = []
    for chap in chapters:
        # Optional: You could query the actual count of questions here if needed
        # For performance, we can hardcode or estimate, or do a separate count query
        response.append({
            "chapterId": chap.chapter_id,
            "chapterName": chap.chapter_name,
            "questionCount": 20 # Placeholder or dynamic
        })
        
    return response

# =======================================================================
# 2. START CHAPTER TEST (Logic to fetch 20 random Qs)
# =======================================================================
@app.post("/tests/start/chapter", response_model=schemas.TestResponse)
async def start_chapter_test(
    request: schemas.StartChapterTestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    chapter_id = request.chapterId
    print(f"--- Starting Test for Chapter ID: {chapter_id} ---")

    # 1. FETCH QUESTIONS
    # We join Question -> Subtopic -> Chapter to filter by chapter_id
    questions_query = (
        select(models.Question)
        .join(models.Subtopic)
        .join(models.Chapter)
        .where(models.Chapter.chapter_id == chapter_id)
        .order_by(func.random()) # Randomize order
        .limit(request.questionCount)
        .options(selectinload(models.Question.options)) # Load options efficiently
    )
    
    questions = (await db.execute(questions_query)).scalars().all()
    
    if not questions:
        # Fallback: detailed error if chapter exists but is empty
        raise HTTPException(
            status_code=404, 
            detail="No questions found for this chapter in the database."
        )

    # 2. FETCH CHAPTER DETAILS (For Test Name)
    chapter_res = await db.get(models.Chapter, chapter_id)
    test_name = f"{chapter_res.chapter_name} Practice" if chapter_res else "Chapter Practice"

    # 3. CREATE TEST SESSION
    new_test = models.Test(
        test_id=str(uuid.uuid4()),
        user_id=current_user.user_id,
        template_id=None, # No template needed
        test_name=test_name,
        test_type=models.TestTypeEnum.CHAPTER_TEST,
        status=models.TestStatusEnum.IN_PROGRESS,
        start_time=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    db.add(new_test)
    
    # 4. LINK QUESTIONS TO TEST
    sections_map = {}
    
    for q in questions:
        # Create TestAnswer entry (the link)
        db.add(models.TestAnswer(
            answer_id=str(uuid.uuid4()), 
            test=new_test, 
            question=q
        ))
        
        # Format for JSON Response
        q_type = q.question_type.value if q.question_type else "MCSC"
        if q_type not in sections_map: sections_map[q_type] = []
        
        sections_map[q_type].append({
            "questionId": q.question_id, 
            "questionText": q.question_text,
            "options": [{"optionId": o.option_id, "optionText": o.option_text} for o in q.options],
            "positiveMarks": q.positive_marks, 
            "negativeMarks": q.negative_marks
        })

    await db.commit()
    await db.refresh(new_test)

    # 5. CONSTRUCT FINAL RESPONSE
    final_sections = [
        {"sectionId": f"{qt.lower()}_sec", "sectionName": f"Section - {qt}", "questionType": qt, "questions": qs}
        for qt, qs in sections_map.items()
    ]

    return {
        "sessionId": new_test.test_id, 
        "testId": new_test.test_id,
        "testName": new_test.test_name, 
        "durationInSeconds": 3600, # 60 Minutes standard for chapter practice
        "sections": final_sections
    }

# =======================================================================
# 3. START SUBJECT TEST (Logic to fetch random Qs for a Subject)
# =======================================================================
@app.post("/tests/start/subject", response_model=schemas.TestResponse)
async def start_subject_test(
    request: schemas.StartSubjectTestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    subject_id = request.subjectId
    print(f"--- Starting Test for Subject ID: {subject_id} ---")

    # 1. FETCH QUESTIONS
    # Logic: Join Question -> Subtopic -> Chapter -> Subject
    questions_query = (
        select(models.Question)
        .join(models.Subtopic)
        .join(models.Chapter)
        .join(models.Subject)
        .where(models.Subject.subject_id == subject_id)
        .order_by(func.random()) # Randomize order
        .limit(request.questionCount)
        .options(selectinload(models.Question.options)) # Eager load options
    )
    
    questions = (await db.execute(questions_query)).scalars().all()
    
    if not questions:
        raise HTTPException(
            status_code=404, 
            detail="No questions found for this subject in the database."
        )

    # 2. FETCH SUBJECT NAME (For Test Name)
    subject_res = await db.get(models.Subject, subject_id)
    # If subject name is Physics, test name becomes "Physics Subject Test"
    test_name = f"{subject_res.subject_name} Subject Test" if subject_res else "Subject Practice"

    # 3. CREATE TEST SESSION
    new_test = models.Test(
        test_id=str(uuid.uuid4()),
        user_id=current_user.user_id,
        template_id=None,
        test_name=test_name,
        test_type=models.TestTypeEnum.SUBJECT_TEST, # Ensure this Enum exists in your models
        status=models.TestStatusEnum.IN_PROGRESS,
        start_time=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    db.add(new_test)
    
    # 4. LINK QUESTIONS TO TEST
    sections_map = {}
    
    for q in questions:
        # Create the database link
        db.add(models.TestAnswer(
            answer_id=str(uuid.uuid4()), 
            test=new_test, 
            question=q
        ))
        
        # Format for JSON Response
        q_type = q.question_type.value if q.question_type else "MCSC"
        if q_type not in sections_map: sections_map[q_type] = []
        
        sections_map[q_type].append({
            "questionId": q.question_id, 
            "questionText": q.question_text,
            "options": [{"optionId": o.option_id, "optionText": o.option_text} for o in q.options],
            "positiveMarks": q.positive_marks, 
            "negativeMarks": q.negative_marks
        })

    await db.commit()
    await db.refresh(new_test)

    # 5. CONSTRUCT FINAL RESPONSE
    final_sections = [
        {"sectionId": f"{qt.lower()}_sec", "sectionName": f"Section - {qt}", "questionType": qt, "questions": qs}
        for qt, qs in sections_map.items()
    ]

    return {
        "sessionId": new_test.test_id, 
        "testId": new_test.test_id,
        "testName": new_test.test_name, 
        "durationInSeconds": 3600 * 3, # Usually 3 hours for a full subject block, or adjust as needed
        "sections": final_sections
    }

# app/main.py

@app.get("/tests/{test_id}", response_model=schemas.TestResponse)
async def get_existing_test(
    test_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 1. Fetch Test with all nested relations
    query = (
        select(models.Test)
        .where(
            models.Test.test_id == test_id,
            models.Test.user_id == current_user.user_id
        )
        .options(
            selectinload(models.Test.answers)
            .selectinload(models.TestAnswer.question)
            .selectinload(models.Question.options),
            selectinload(models.Test.answers)
            .selectinload(models.TestAnswer.selections) # Load user selections
        )
    )
    result = await db.execute(query)
    test = result.scalars().first()
    
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Check if review mode is allowed
    is_review_mode = (test.status == models.TestStatusEnum.COMPLETED)

    # 2. Format Response
    sections_map = {}
    for ans in test.answers:
        q = ans.question
        q_type = q.question_type.value if q.question_type else "MCSC"
        
        if q_type not in sections_map: sections_map[q_type] = []
        
        # Determine User Selections for this specific answer
        user_selected_ids = {sel.selected_option_id for sel in ans.selections}
        
        # Format Options
        options_list = []
        for o in q.options:
            opt_data = {
                "optionId": o.option_id,
                "optionText": o.option_text,
                # ONLY send correctness info if test is completed
                "isCorrect": o.is_correct if is_review_mode else False, 
                "isSelected": (o.option_id in user_selected_ids) if is_review_mode else False
            }
            options_list.append(opt_data)

        # Numerical Answer Handling
        correct_int = None
        user_int = None
        if is_review_mode and q.question_type == models.QuestionTypeEnum.NUMERICAL:
            user_int = ans.integer_answer
            # Logic to extract correct integer (assuming it's stored or extracted from options)
            # For this example, we assume we extract it from the first correct option text
            for o in q.options:
                 if o.is_correct:
                     try:
                         correct_int = int(float(o.option_text))
                     except: 
                         pass

        sections_map[q_type].append({
            "questionId": q.question_id,
            "questionText": q.question_text,
            "options": options_list,
            "positiveMarks": q.positive_marks,
            "negativeMarks": q.negative_marks,
            # Extra fields for review
            "userIntegerAnswer": user_int,
            "correctIntegerAnswer": correct_int,
            "status": ans.status.value if is_review_mode else "UNATTEMPTED"
        })

    final_sections = [
        {"sectionId": f"{qt.lower()}_sec", "sectionName": f"Section - {qt}", "questionType": qt, "questions": qs}
        for qt, qs in sections_map.items()
    ]

    return {
        "sessionId": test.test_id,
        "testId": test.test_id,
        "testName": test.test_name,
        "durationInSeconds": 3600, 
        "sections": final_sections
    }