# gemini_processor.py
import json
import google.generativeai as genai

def process_all_with_gemini(extracted_data, source_type, source_details, full_syllabus):
    """
    Sends the entire list of extracted questions to the Gemini API in a single call.
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
    4.  **Classify `subtopic_name`:** Based on the identified subject, look into the syllabus JSON and choose the single most appropriate `subtopic_name`. **CRITICAL**: The `subtopic_name` in your output must be an exact, case-sensitive, character-for-character copy of a name from the list. Do not alter, summarize, or rephrase it in any way.
    5.  **Format Options:** Populate the `option_A`, `option_B`, `option_C`, and `option_D` fields. If a question has no options, set the unused fields to `null`.
    6.  **Determine `question_type`:** Use "MCMC" for multiple correct, "MCSC" for single correct, "NUMERICAL" for integer answers.
    7.  **Determine `difficulty_level`:** Classify as "EASY", "MEDIUM", or "HARD".
    8.  **Extract Marks:** Find positive and negative marks from the `section_instructions`.
    9.  **CRITICAL JSON RULE:** The JSON you generate must be perfectly valid. In JSON strings, every literal backslash `\` must be escaped with another backslash, becoming `\\`. This is essential for LaTeX formulas. **Example:** To represent the LaTeX `\\sqrt{{x}}`, the JSON string must be `"$\\\\sqrt{{x}}$"`. **Do not** write `"$\\sqrt{{x}}$"`, as this is invalid and will cause a parsing error.
    10. **Strict Schema Adherence:** The final output must be ONLY a valid JSON array matching the schema below.

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

    print("    - Sending all questions to Gemini in a single batch...")
    response = model.generate_content(prompt)
    try:
        cleaned_response = response.text.strip().lstrip("```json").rstrip("```")
        return json.loads(cleaned_response)
    except (json.JSONDecodeError, AttributeError):
        print(f"    - Error: Failed to decode JSON from Gemini response.")
        print(f"    - Raw Response Snippet: {response.text[:200]}...")
        raise ValueError("Gemini API did not return valid JSON.")