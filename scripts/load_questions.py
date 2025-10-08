import asyncio
import json
import os
import uuid
from sqlalchemy import select

# Add the project root to the Python path to allow absolute imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now you can use absolute imports from your 'app' package
from app.database import SessionLocal
from app.models import (
    Exam, Question, QuestionOption, QuestionExamApplicability,
    DifficultyLevelEnum, QuestionTypeEnum, SourceEnum, AIValidationStatusEnum
)

# --- Configuration ---
# Directory where your JSON files are stored
SEED_DATA_DIR = os.path.join(os.path.dirname(__file__), 'seed_data')
# The Exam ID for "Jee Advanced" as requested
JEE_ADVANCED_EXAM_ID = 3
JEE_ADVANCED_EXAM_NAME = "JEE Advanced"

async def get_or_create(session, model, defaults=None, **kwargs):
    """Helper function to get an instance if it exists, or create it if it doesn't."""
    result = await session.execute(select(model).filter_by(**kwargs))
    instance = result.scalars().first()
    if instance:
        return instance
    else:
        kwargs.update(defaults or {})
        instance = model(**kwargs)
        session.add(instance)
        await session.flush()
        return instance

async def load_questions_from_json():
    """
    Main function to read JSON files and load them into the database.
    Assumes Subjects, Chapters, and Subtopics already exist.
    """
    print("🚀 Starting question loading script...")
    db = SessionLocal()

    try:
        jee_exam = await get_or_create(db, Exam, exam_id=JEE_ADVANCED_EXAM_ID, defaults={'exam_name': JEE_ADVANCED_EXAM_NAME})

        json_files = [f for f in os.listdir(SEED_DATA_DIR) if f.endswith('.json')]
        if not json_files:
            print("❌ No JSON files found in /scripts/seed_data. Exiting.")
            return

        print(f"Found {len(json_files)} JSON files to process.")

        for file_name in json_files:
            file_path = os.path.join(SEED_DATA_DIR, file_name)
            print(f"\nProcessing file: {file_name}...")

            with open(file_path, 'r') as f:
                questions_data = json.load(f)

            for q_data in questions_data:
                # Check for existing questions to prevent duplicates
                existing_question_result = await db.execute(select(Question).where(Question.question_text == q_data['question_text']))
                if existing_question_result.scalars().first():
                    print(f"  - Skipping existing question: '{q_data['question_text'][:50]}...'")
                    continue

                # Validate that subtopic_id is present
                if 'subtopic_id' not in q_data or not q_data['subtopic_id']:
                    print(f"  - ❌ Skipping question due to missing 'subtopic_id': '{q_data['question_text'][:50]}...'")
                    continue

                # --- Map incoming question types explicitly ---
                q_type_str = q_data['question_type']
                if q_type_str == "MCMC":
                    q_type_enum = QuestionTypeEnum.MCMC
                elif q_type_str == "MCSC":
                    q_type_enum = QuestionTypeEnum.MCSC
                elif q_type_str == "NUMERICAL":
                    q_type_enum = QuestionTypeEnum.NUMERICAL
                else:
                    # If the type is none of the above, we log a warning and skip it.
                    print(f"  - ⚠️  Unknown question type '{q_type_str}'. Skipping question.")
                    continue
                # --- END MAPPING ---

                new_question = Question(
                    question_id=str(uuid.uuid4()),
                    question_text=q_data['question_text'],
                    image_url=q_data.get('image_url'),
                    question_type=q_type_enum,
                    subtopic_id=q_data['subtopic_id'],
                    difficulty_level=DifficultyLevelEnum[q_data['difficulty_level'].upper()],
                    source=SourceEnum[q_data['source'].replace('IIT-JEE', 'PYQ')], # Normalize source name
                    source_details=q_data.get('source_details'),
                    positive_marks=q_data['positive_marks'],
                    negative_marks=abs(q_data['negative_marks']),
                    solution_explanation=None,
                    vector=None,
                    ai_validation_status=AIValidationStatusEnum.PENDING,
                )

                # Create Question Options
                options = []
                for option_key in ['option_A', 'option_B', 'option_C', 'option_D']:
                    option_text = q_data.get(option_key)
                    if option_text:
                        new_option = QuestionOption(
                            option_id=str(uuid.uuid4()),
                            question_id=new_question.question_id,
                            option_text=option_text,
                            is_correct=False
                        )
                        options.append(new_option)
                new_question.options = options

                # Link Question to Exam
                exam_applicability = QuestionExamApplicability(
                    question_id=new_question.question_id,
                    exam_id=jee_exam.exam_id
                )

                db.add(new_question)
                db.add(exam_applicability)

                print(f"  - Added question: '{new_question.question_text[:50]}...'")

            # Commit changes after processing all questions in the current file
            await db.commit()
            print(f"✅ Committed questions from {file_name}.")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        await db.rollback()
    finally:
        await db.close()

    print("\n🎉 Question loading script finished.")

if __name__ == "__main__":
    asyncio.run(load_questions_from_json())