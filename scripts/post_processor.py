# post_processor.py
import json
from thefuzz import process

def map_subtopics_to_ids(llm_questions, syllabus_data, similarity_threshold=90):
    """Maps subtopic names to IDs using exact and fuzzy matching."""
    lookup_map = {}
    for subject, chapters in syllabus_data.get("syllabus", {}).items():
        for chapter, subtopics in chapters.items():
            for subtopic in subtopics:
                lookup_map[subtopic["subtopic_name"]] = subtopic["subtopic_id"]
    
    valid_subtopic_names = list(lookup_map.keys())
    database_ready_questions = []
    skipped_count = 0
    fuzzy_corrections = 0

    for q in llm_questions:
        subtopic_name_from_llm = q.get("subtopic_name")
        subtopic_id = None
        
        if subtopic_name_from_llm in lookup_map:
            subtopic_id = lookup_map[subtopic_name_from_llm]
        elif subtopic_name_from_llm:
            best_match, score = process.extractOne(subtopic_name_from_llm, valid_subtopic_names)
            if score >= similarity_threshold:
                subtopic_id = lookup_map[best_match]
                fuzzy_corrections += 1
        
        if subtopic_id:
            db_question = q.copy()
            db_question["subtopic_id"] = subtopic_id
            del db_question["subtopic_name"]
            database_ready_questions.append(db_question)
        else:
            skipped_count += 1
            print(f"    - Warning: Could not match subtopic '{subtopic_name_from_llm}'.")

    print(f"    - {fuzzy_corrections} corrections made via fuzzy matching.")
    if skipped_count > 0:
        print(f"    - {skipped_count} questions skipped due to missing subtopics.")
    return database_ready_questions