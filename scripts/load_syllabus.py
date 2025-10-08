import asyncio
import json
import os
from sqlalchemy import select

# Add the project root to the Python path to allow absolute imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now you can use absolute imports from your 'app' package
from app.database import SessionLocal
from app.models import Subject, Chapter, Subtopic

# --- Configuration ---
SYLLABUS_FILE_PATH = os.path.join(os.path.dirname(__file__), 'jee_advanced_syllabus.json')

async def get_or_create(session, model, defaults=None, **kwargs):
    """
    Helper function to get an instance if it exists, or create it if it doesn't.
    """
    # Check if an instance with the primary key exists
    pk_value = kwargs.get(f'{model.__tablename__[:-1]}_id') # e.g., 'subtopic_id'
    if pk_value:
        instance = await session.get(model, pk_value)
        if instance:
            return instance

    # Otherwise, check by other unique attributes
    result = await session.execute(select(model).filter_by(**kwargs))
    instance = result.scalars().first()
    if instance:
        return instance
    else:
        # If not found, create a new one
        kwargs.update(defaults or {})
        instance = model(**kwargs)
        session.add(instance)
        await session.flush() # flush to get the ID for relationships
        return instance

async def load_syllabus_from_json():
    """
    Main function to read the syllabus JSON and populate the hierarchy tables.
    """
    print("🚀 Starting syllabus loading script...")
    
    if not os.path.exists(SYLLABUS_FILE_PATH):
        print(f"❌ Error: Syllabus file not found at '{SYLLABUS_FILE_PATH}'. Exiting.")
        return

    db = SessionLocal()
    try:
        with open(SYLLABUS_FILE_PATH, 'r') as f:
            data = json.load(f)

        syllabus = data.get("syllabus", {})
        if not syllabus:
            print("❌ No 'syllabus' key found in the JSON file. Exiting.")
            return

        print(f"Found {len(syllabus.keys())} subjects to process: {list(syllabus.keys())}")

        for subject_name, chapters in syllabus.items():
            # --- 1. Create or Get Subject ---
            subject_obj = await get_or_create(db, Subject, subject_name=subject_name.capitalize())
            print(f"\nProcessing Subject: {subject_obj.subject_name} (ID: {subject_obj.subject_id})")

            for chapter_name, subtopics in chapters.items():
                # --- 2. Create or Get Chapter ---
                chapter_obj = await get_or_create(
                    db, Chapter,
                    chapter_name=chapter_name.capitalize(),
                    subject_id=subject_obj.subject_id
                )
                print(f"  - Processing Chapter: {chapter_obj.chapter_name} (ID: {chapter_obj.chapter_id})")

                for subtopic_data in subtopics:
                    subtopic_id = subtopic_data.get('subtopic_id')
                    subtopic_name = subtopic_data.get('subtopic_name')
                    
                    if not subtopic_id or not subtopic_name:
                        print(f"    - ⚠️ Skipping invalid subtopic entry: {subtopic_data}")
                        continue

                    # --- 3. Create or Get Subtopic ---
                    # We use the provided ID as the primary key
                    subtopic_obj = await get_or_create(
                        db, Subtopic,
                        subtopic_id=subtopic_id,
                        defaults={
                            'subtopic_name': subtopic_name,
                            'chapter_id': chapter_obj.chapter_id
                        }
                    )
                    print(f"    - Synced Subtopic: {subtopic_obj.subtopic_name} (ID: {subtopic_obj.subtopic_id})")
        
        # Commit all the changes at the end
        await db.commit()
        print("\n✅ Successfully committed all syllabus data to the database.")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        await db.rollback()
    finally:
        await db.close()

    print("\n🎉 Syllabus loading script finished.")

if __name__ == "__main__":
    # Allows you to run the script directly from the command line
    asyncio.run(load_syllabus_from_json())