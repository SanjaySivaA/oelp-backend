# run_pipeline.py
import os
import json
import time
import logging
from dotenv import load_dotenv
import google.generativeai as genai

from pdf_extractor import analyze_and_extract_with_instructions
from gemini_processor import process_all_with_gemini # <-- Import the single-call function
from post_processor import map_subtopics_to_ids

# --- Setup ---
load_dotenv()
os.makedirs("seed_data", exist_ok=True)
os.makedirs("llm_outputs", exist_ok=True)
os.makedirs("logs", exist_ok=True)
os.makedirs("pdfs", exist_ok=True)

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

def main():
    print("--- 🚀 Starting PDF Processing Pipeline (Single-Call Mode) ---")
    
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
        
        print(f"\n--- Processing file {i+1}/{len(pdf_files)}: {filename} ---")
        file_start_time = time.time()
        
        try:
            # Step 1: Extract Raw Data
            raw_data = analyze_and_extract_with_instructions(pdf_path)
            print(f"  [1/3] Extraction complete ({len(raw_data)} questions found).")

            # Step 2: Process with Gemini (Single Call)
            source_details = base_name.replace('_', ' ').title()
            llm_output_data = process_all_with_gemini(raw_data, SOURCE_TYPE, source_details, syllabus)
            
            with open(f"llm_outputs/{base_name}.json", 'w') as f:
                json.dump(llm_output_data, f, indent=2)
            print(f"  [2/3] Gemini processing complete.")

            # Step 3: Post-process to map subtopic IDs
            database_ready_data = map_subtopics_to_ids(llm_output_data, syllabus)
            
            output_path = os.path.join("seed_data", f"{base_name}.json")
            with open(output_path, 'w') as f:
                json.dump(database_ready_data, f, indent=2)
            
            file_duration = time.time() - file_start_time
            print(f"  [3/3] ✅ Success! Final data saved to {output_path} in {file_duration:.2f}s.")

        except Exception as e:
            print(f"  [✗] ERROR: Failed to process {filename}. See logs/pipeline_errors.log for details.")
            logging.error(f"Failed to process file: {filename}\n  Error: {e}", exc_info=True)
            continue
    
    print(f"\n--- Pipeline Finished ---")

if __name__ == "__main__":
    main()