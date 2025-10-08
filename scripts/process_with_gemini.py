# process_with_gemini.py

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from pdf_extractor import analyze_and_extract_with_instructions

# --- Configuration ---
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# --- User-defined Constants ---
FILE = "2017_1"
PDF_FILE_PATH = f"pdfs/{FILE}.pdf"
SYLLABUS_FILE_PATH = "jee_advanced_syllabus.json" 
SOURCE_TYPE = "PYQ"
SOURCE_DETAILS = "JEE Advanced 2017 Paper 1" 

def process_with_gemini(extracted_data, source_type, source_details, full_syllabus):
    """
    Sends extracted data and the full syllabus to the Gemini API for dynamic
    classification, LaTeX formatting, and structuring.
    """
    model = genai.GenerativeModel('gemini-2.5-pro')
    syllabus_json_string = json.dumps(full_syllabus, indent=2)
    data_json_string = json.dumps(extracted_data, indent=2)

    schema = """
    [
      {
        "question_text": "String (formatted with Markdown and LaTeX for math)",
        "image_url": "null",
        "question_type": "String Enum ('MCSC', 'MCMC', 'NUMERICAL')",
        "subject": "String ('Physics', 'Chemistry', 'Mathematics')",
        "subtopic_name": "String (Must be one of the subtopics from the provided syllabus)",
        "difficulty_level": "String Enum ('EASY', 'MEDIUM', 'HARD')",
        "option_A": "String or null (formatted with Markdown and LaTeX)",
        "option_B": "String or null (formatted with Markdown and LaTeX)",
        "option_C": "String or null (formatted with Markdown and LaTeX)",
        "option_D": "String or null (formatted with Markdown and LaTeX)",
        "correct_option": "String (e.g., 'A', 'B,C') or null",
        "source": "String", "source_details": "String",
        "positive_marks": "Integer", "negative_marks": "Integer",
        "solution_explanation": "null"
      }
    ]
    """
    
    # --- PROMPT INSTRUCTION CHANGE HERE ---
    # Added a new instruction for LaTeX formatting.
    prompt = f"""
    You are an expert data processor for an educational platform. Your task is to transform a raw JSON object into a clean JSON array that strictly adheres to the provided schema.

    **Syllabus for All Subjects:**
    ```json
    {syllabus_json_string}
    ```

    **Detailed Instructions:**
    1.  **For each question in the Raw Extracted Data, perform the following steps:**
    2.  **Format Mathematical Expressions:** Identify all mathematical formulas, variables, and symbols in the `question_text` and all `option_` fields. Convert them into standard LaTeX format, enclosed in single dollar signs (`$...$`). For example, transform "The value is sqrt(A/(B^2))" into "The value is $\\sqrt{{\\frac{{A}}{{B^2}}}}$". Ensure even single variables like 'x' or 'v' are formatted as '$x$' or '$v$'.
    3.  **Determine `subject`:** Read the `section_instructions` to determine if the question is from 'Physics', 'Chemistry', or 'Mathematics'.
    4.  **Classify `subtopic_name`:** For each question, you MUST choose the most relevant subtopic from the following list. **CRITICAL**: The `subtopic_name` in your output must be an exact, case-sensitive, character-for-character copy of a name from this list. Do not alter, summarize, or rephrase it in any way.
    5.  **Format Options:** Populate the `option_A`, `option_B`, `option_C`, and `option_D` fields. If a question has no options, set the unused fields to `null`.
    6.  **Determine `question_type`:** Use "MCMC" for multiple correct, "MCSC" for single correct, "NUMERICAL" for integer answers.
    7.  **Determine `difficulty_level`:** Classify as "EASY", "MEDIUM", or "HARD".
    8.  **Extract Marks:** Find positive and negative marks from the `section_instructions`.
    9.  **Strict Schema Adherence:** The final output must be ONLY a valid JSON array matching the schema below.

    **Target Schema:**
    ```json
    {schema}
    ```

    **Raw Extracted Data:**
    ```json
    {data_json_string}
    ```

    **Your Output (JSON Array Only):**
    """

    print("--- Sending data to Gemini for processing and LaTeX formatting... ---")
    response = model.generate_content(prompt)
    
    try:
        cleaned_response = response.text.strip().lstrip("```json").rstrip("```")
        return json.loads(cleaned_response)
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"--- Error processing Gemini response: {e} ---")
        print(f"--- Raw Response Text: ---\n{response.text}")
        return None

# --- Main execution block ---
if __name__ == "__main__":
    if not os.path.exists(PDF_FILE_PATH):
        print(f"Error: PDF file not found at '{PDF_FILE_PATH}'")
    elif not os.path.exists(SYLLABUS_FILE_PATH):
        print(f"Error: Syllabus file not found at '{SYLLABUS_FILE_PATH}'")
    else:
        with open(SYLLABUS_FILE_PATH, 'r') as f:
            syllabus = json.load(f)
        
        print(f"--- Successfully loaded syllabus with subjects: {list(syllabus.get('syllabus', {}).keys())}. ---")
        print(f"--- Starting extraction from {PDF_FILE_PATH}... ---")
        raw_data = analyze_and_extract_with_instructions(PDF_FILE_PATH)
        
        if raw_data:
            print(f"--- Successfully extracted {len(raw_data)} questions. ---")
            
            final_json_data = process_with_gemini(raw_data, SOURCE_TYPE, SOURCE_DETAILS, syllabus)
            
            if final_json_data:
                print("--- Successfully received and parsed JSON from Gemini! ---")
                
                with open(f"llm_outputs/{FILE}.json", "w") as f:
                    json.dump(final_json_data, f, indent=2)
                
                print(f"--- Clean, structured JSON data saved to {FILE}.json ---")