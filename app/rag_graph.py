# app/rag_graph.py

import os
import json
import re
from typing import TypedDict, Dict, Any
from langgraph.graph import StateGraph, END
import google.generativeai as genai

# --- 1. Setup Google AI ---
if os.getenv("GOOGLE_API_KEY"):
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel("gemini-2.0-flash")

# --- 2. Define the State ---
class AgentState(TypedDict):
    original_question: str
    subject: str # Can be "Unknown"
    generated_question_json: Dict[str, Any]
    feedback: str 
    attempts: int 

# --- Helper to Clean JSON ---
def clean_and_repair_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"): text = text[7:]
    elif text.startswith("```"): text = text[3:]
    if text.endswith("```"): text = text[:-3]
    text = text.strip()
    # Fix latex backslashes
    try:
        text = re.sub(r'(?<!\\)\\(?!["\\/bfnrtu])', r'\\\\', text)
    except Exception:
        pass
    return text

# --- 3. Define Nodes ---

def generator_node(state: AgentState):
    attempt = state.get('attempts', 0) + 1
    print(f"   [GRAPH] Generating... (Attempt {attempt})")
    
    subject_context = state.get("subject", "Unknown")
    
    # PROMPT UPDATE: Asked LLM to identify topic if unknown
    prompt = f"""
    You are an expert exam setter for JEE/NEET. 
    
    Input Context:
    1. Student answered this question WRONG.
    2. Question Text: "{state['original_question']}"
    3. Subject Context: {subject_context}

    Task:
    1. Analyze the Question Text to identify the specific academic concept (e.g., Rotational Motion, Organic Chemistry, Calculus).
    2. Create 1 NEW, UNIQUE Multiple Choice Question (MCSC) testing that SAME concept.
    3. The difficulty should be slightly lower than the original to build confidence.

    IMPORTANT FORMATTING:
    - Return ONLY valid raw JSON.
    - **DOUBLE ESCAPE ALL LATEX BACKSLASHES** (e.g., \\\\sigma, \\\\frac).
    
    JSON Schema:
    {{
      "detected_concept": "str (e.g. 'Thermodynamics')",
      "question_text": "str",
      "option_A": "str",
      "option_B": "str",
      "option_C": "str",
      "option_D": "str",
      "correct_option": "A",
      "solution_explanation": "str"
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        cleaned_text = clean_and_repair_json(response.text)
        data = json.loads(cleaned_text)
        
        return {
            "generated_question_json": data, 
            "attempts": attempt
        }
    except Exception as e:
        return {"feedback": f"Generation Error: {e}", "attempts": attempt}

def critic_node(state: AgentState):
    data = state.get("generated_question_json")
    if not data or not data.get("question_text"):
        return {"feedback": "Invalid JSON structure"}
    return {"feedback": "valid"}

# --- 4. Logic & Graph ---
def should_continue(state: AgentState):
    if state.get("feedback") == "valid": return "end"
    if state.get("attempts", 0) >= 3: return "end" # Allow 3 attempts
    return "retry"

workflow = StateGraph(AgentState)
workflow.add_node("generator", generator_node)
workflow.add_node("critic", critic_node)
workflow.set_entry_point("generator")
workflow.add_edge("generator", "critic")
workflow.add_conditional_edges("critic", should_continue, {"end": END, "retry": "generator"})

app_graph = workflow.compile()