# run_pipeline.py
import os
import json
import time
import logging
import re
from dotenv import load_dotenv
import google.generativeai as genai

from pdf_extractor import analyze_and_extract_with_instructions
from gemini_processor import get_gemini_response # <-- Updated import
from post_processor import map_subtopics_to_ids

# --- Setup ---
load_dotenv()
os.makedirs("seed_data", exist_ok=True)
os.makedirs("llm_outputs", exist_ok=True)
os.makedirs("logs", exist_ok=True)
os.makedirs("pdfs", exist_ok=True)
os.makedirs("failed_outputs", exist_ok=True) # <-- New directory for bad outputs


try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file or environment variables.")
    genai.configure(api_key=api_key)
    print("--- Gemini API key configured successfully. ---")
except Exception as e:
    print(f"FATAL ERROR: Could not configure Gemini API. {e}")
    exit() # Exit the script if the key is not found

logging.basicConfig(
    filename='logs/pipeline_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Configuration ---
PDF_DIR = "pdfs"
SYLLABUS_FILE = "jee_advanced_syllabus.json"
SOURCE_TYPE = "PYQ"

def fix_and_parse_json(raw_text):
    """
    Cleans the raw text from the LLM and attempts to parse it.
    Includes a step to programmatically fix common JSON errors like unescaped backslashes.
    """
    cleaned_text = raw_text.strip().lstrip("```json").rstrip("```")
    
    try:
        # First attempt: parse the text as is
        return json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        # If it fails, attempt to fix the common backslash error
        print("    - Initial JSON parse failed. Attempting to fix backslash errors...")
        # This regex finds a backslash that is NOT followed by another backslash or a quote
        # and replaces it with a double backslash.
        fixed_text = re.sub(r'(?<!\\)\\(?!["\\/bfnrtu])', r'\\\\', cleaned_text)
        
        try:
            # Second attempt: parse the fixed text
            return json.loads(fixed_text)
        except json.JSONDecodeError:
            # If it still fails, we give up and raise the error to be logged.
            raise e


def main():
    print("--- 🚀 Starting PDF Processing Pipeline ---")
    
    try:
        with open(SYLLABUS_FILE, 'r') as f:
            syllabus = json.load(f)
    except FileNotFoundError:
        print(f"FATAL ERROR: {SYLLABUS_FILE} not found. Exiting.")
        return

    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print("No PDF files found in the 'pdfs/' directory. Exiting.")
        return
        
    for i, filename in enumerate(pdf_files):
        pdf_path = os.path.join(PDF_DIR, filename)
        base_name = os.path.splitext(filename)[0]
        raw_llm_output = "" # Variable to hold the raw text for error logging
        
        print(f"\n--- Processing file {i+1}/{len(pdf_files)}: {filename} ---")
        
        try:
            # Step 1: Extract
            raw_data = analyze_and_extract_with_instructions(pdf_path)
            print(f"  [1/4] Extraction complete ({len(raw_data)} questions found).")

            # Step 2: Get Raw Response from Gemini
            source_details = base_name.replace('_', ' ').title()
            raw_llm_output = get_gemini_response(raw_data, SOURCE_TYPE, source_details, syllabus)
            print(f"  [2/4] Gemini response received.")

            # Step 3: Clean, Fix, and Parse the JSON
            llm_output_data = fix_and_parse_json(raw_llm_output)
            with open(f"llm_outputs/{base_name}.json", 'w') as f:
                json.dump(llm_output_data, f, indent=2)
            print(f"  [3/4] JSON parsed and saved successfully.")

            # Step 4: Post-process
            database_ready_data = map_subtopics_to_ids(llm_output_data, syllabus)
            output_path = os.path.join("seed_data", f"{base_name}.json")
            with open(output_path, 'w') as f:
                json.dump(database_ready_data, f, indent=2)
            
            print(f"  [4/4] ✅ Success! Final data saved to {output_path}.")

        except Exception as e:
            print(f"  [✗] ERROR: Failed to process {filename}. Saving raw output for review.")
            logging.error(f"Failed to process file: {filename}\n  Error: {e}", exc_info=True)
            
            # This is the new part: save the bad output so you can see it
            if raw_llm_output:
                failed_path = os.path.join("failed_outputs", f"{base_name}_failed.txt")
                with open(failed_path, "w") as f:
                    f.write(raw_llm_output)
                print(f"      -> Raw LLM output saved to {failed_path}")
            continue
    
    print(f"\n--- Pipeline Finished ---")

if __name__ == "__main__":
    main()