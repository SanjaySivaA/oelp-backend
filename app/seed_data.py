# app/seed_data.py

import asyncio
import json
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from pathlib import Path
from datetime import datetime, timedelta # Import timedelta

from sqlalchemy import select

# Import your models. Make sure all necessary enums are imported.
from app.models import (
    Base, User, Exam, Subject, Chapter, Subtopic, Question, QuestionOption, Test, # Added Test
    QuestionType, DifficultyLevel, SourceEnum, TestStatusEnum, TestTypeEnum, UserSubjectAnalytics # Added TestStatusEnum and UserSubjectAnalytics
)
from app.main import get_password_hash

DATABASE_URL = "postgresql+asyncpg://karthik:x6AAfJIhGnzNfqHAng43zy2pgUwvuCXa@dpg-d3v5lj8gjchc73f95adg-a.singapore-postgres.render.com/oelp_database" # Ensure this is your current, correct URL
ENGINE = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(ENGINE, class_=AsyncSession, expire_on_commit=False)

async def seed_database():
    async with ENGINE.begin() as conn:
        print("--- Wiping the database for a clean start... ---")
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        print("--- Seeding database with user, subjects, questions, and sample analytics... ---")

        # 1. Create User and Exam
        user = User(user_id="user_seed_123", email="test@example.com", password_hash=get_password_hash("password123"), name="Test User")
        exam = Exam(exam_id=1, exam_name="JEE Main")
        db.add_all([user, exam])
        print("-> Created default user and exam.")
        await db.commit() # Commit early

        # 2. Load questions from JSON (Needed for question seeding)
        base_dir = Path(__file__).resolve().parent.parent
        json_file_path = base_dir / "assets" / "2017_1.json"
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                questions_data = json.load(f)
        except Exception as e:
            print(f"ERROR reading questions file: {e}")
            return # Stop if questions can't be read

        # 3. Create Subjects, Chapters, Subtopics, and Questions in the DB
        subjects = {}
        chapters = {}
        subtopics = {}
        question_objects = [] # Store question objects for linking later if needed

        existing_subjects_result = await db.execute(select(Subject))
        for s in existing_subjects_result.scalars().all():
             subjects[s.subject_name] = s

        print("-> Seeding questions...")
        question_count = 0
        for q_json in questions_data:
            subject_name = q_json.get("subject")
            if not subject_name: continue

            current_subject = subjects.get(subject_name)
            if not current_subject:
                current_subject = Subject(subject_name=subject_name)
                db.add(current_subject); await db.flush(); subjects[subject_name] = current_subject
            
            chapter_name = f"Chapter for {subject_name}"
            current_chapter = chapters.get(chapter_name)
            if not current_chapter:
                current_chapter = Chapter(chapter_name=chapter_name, subject=current_subject)
                db.add(current_chapter); await db.flush(); chapters[chapter_name] = current_chapter

            subtopic_name = q_json.get("subtopic_name", "General")
            current_subtopic = subtopics.get(subtopic_name)
            if not current_subtopic:
                current_subtopic = Subtopic(subtopic_name=subtopic_name, chapter=current_chapter)
                db.add(current_subtopic); await db.flush(); subtopics[subtopic_name] = current_subtopic

            try:
                 new_question = Question(
                    question_id=str(uuid.uuid4()), question_text=q_json.get("question_text"),
                    question_type=q_json.get("question_type", "MCSC").strip(),
                    subtopic=current_subtopic, difficulty_level=q_json.get("difficulty_level", "MEDIUM").strip(),
                    source=SourceEnum.COMPETITIVE_EXAM_ARCHIVE,
                    positive_marks=q_json.get("positive_marks", 4), negative_marks=q_json.get("negative_marks", 1)
                 )
                 db.add(new_question); await db.flush(); question_count += 1
                 question_objects.append(new_question) # Keep track if needed
            except ValueError as e: continue # Skip invalid enum questions

            correct_option_str = q_json.get("correct_option")
            correct_letters = []
            if correct_option_str: correct_letters = [letter.strip() for letter in correct_option_str.split(',')]
            
            for letter in ['A', 'B', 'C', 'D']:
                option_text = q_json.get(f"option_{letter}")
                if option_text:
                    db.add(QuestionOption(
                        option_id=str(uuid.uuid4()), question=new_question,
                        option_text=option_text, is_correct=(letter in correct_letters)
                    ))
        
        print(f"-> Successfully seeded {question_count} questions.")
        
        # =======================================================================
        # 4. ADD SAMPLE COMPLETED TESTS
        # =======================================================================
        print("-> Adding sample completed tests...")
        
        # Ensure we have subject IDs for linking
        physics_id = subjects.get("Physics").subject_id if subjects.get("Physics") else None
        chem_id = subjects.get("Chemistry").subject_id if subjects.get("Chemistry") else None
        math_id = subjects.get("Mathematics").subject_id if subjects.get("Mathematics") else None

        tests_to_add = [
            Test(test_id=str(uuid.uuid4()), user_id=user.user_id, subject_id=physics_id, test_name="Sample Physics Test 1", test_type=TestTypeEnum.SUBJECT_TEST, status=TestStatusEnum.COMPLETED, start_time=datetime.utcnow() - timedelta(days=5, hours=1), end_time=datetime.utcnow() - timedelta(days=5), final_score=120),
            Test(test_id=str(uuid.uuid4()), user_id=user.user_id, subject_id=chem_id, test_name="Sample Chemistry Test 1", test_type=TestTypeEnum.SUBJECT_TEST, status=TestStatusEnum.COMPLETED, start_time=datetime.utcnow() - timedelta(days=3, hours=1), end_time=datetime.utcnow() - timedelta(days=3), final_score=95),
            Test(test_id=str(uuid.uuid4()), user_id=user.user_id, subject_id=math_id, test_name="Sample Math Test 1", test_type=TestTypeEnum.SUBJECT_TEST, status=TestStatusEnum.COMPLETED, start_time=datetime.utcnow() - timedelta(days=1, hours=1), end_time=datetime.utcnow() - timedelta(days=1), final_score=150),
        ]
        db.add_all(tests_to_add)
        print(f"-> Added {len(tests_to_add)} sample tests.")

        # =======================================================================
        # 5. ADD SAMPLE SUBJECT ANALYTICS
        # =======================================================================
        print("-> Adding sample subject analytics...")
        analytics_to_add = []
        if physics_id:
            analytics_to_add.append(UserSubjectAnalytics(user_id=user.user_id, exam_id=exam.exam_id, subject_id=physics_id, questions_attempted=50, correct_answers=35, total_time_taken_seconds=3000, last_updated_at=datetime.utcnow()))
        if chem_id:
            analytics_to_add.append(UserSubjectAnalytics(user_id=user.user_id, exam_id=exam.exam_id, subject_id=chem_id, questions_attempted=45, correct_answers=28, total_time_taken_seconds=2800, last_updated_at=datetime.utcnow()))
        if math_id:
             analytics_to_add.append(UserSubjectAnalytics(user_id=user.user_id, exam_id=exam.exam_id, subject_id=math_id, questions_attempted=55, correct_answers=40, total_time_taken_seconds=3500, last_updated_at=datetime.utcnow()))

        db.add_all(analytics_to_add)
        print(f"-> Added {len(analytics_to_add)} sample analytics records.")

        print("-> Committing all changes...")
        await db.commit()
        print("\n--- Database seeding complete with sample data! ---")

if __name__ == "__main__":
    asyncio.run(seed_database())