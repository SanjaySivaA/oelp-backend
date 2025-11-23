# app/rag_service.py
import fitz, re, uuid, asyncio, json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from .config import settings
from . import models

class RAGService:
    def __init__(self):
        print("Initializing RAG system...")
        self.embedding_model = SentenceTransformer('all-mpnet-base-v2')
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.parser_model = genai.GenerativeModel('gemini-2.0-flash') # Using the stable model
        print("RAG system ready.")

    async def _parse_questions_with_ai(self, page_text: str) -> list[dict]:
        """Uses Gemini to parse text from a single page into structured question data."""
        if not page_text.strip():
            return []
            
        print("Sending page text to Gemini for structured parsing...")
        prompt = f"""
        You are an expert data extractor for JEE and NEET question papers.
        Analyze the following text from a single page. Identify each distinct question.
        Return a valid JSON array where each object represents one question.
        
        For each question, provide:
        1. "question_text": The full question.
        2. "question_type": Classify as "MCSC" for multiple choice, "NUM" for numerical.
        3. "options": An array of strings for each choice. For "NUM" questions, provide an empty array.

        Respond ONLY with the JSON array. Do not include any other text or formatting.
        TEXT TO ANALYZE: --- {page_text} ---
        """
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=8192  # Set a high limit for the JSON output
        )
        try:
            response = await self.parser_model.generate_content_async(prompt)
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(cleaned_response)
        except Exception as e:
            print(f"Error parsing page with Gemini: {e}")
            return []

    async def process_and_store_pdf(self, db: AsyncSession, pdf_content: bytes, source_name: str) -> int:
        """Uses an improved AI prompt to parse a PDF and stores structured questions."""
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        full_text = "".join(page.get_text() for page in doc)
        doc.close()

        if not full_text: return 0

        structured_questions = await self._parse_questions_with_ai(full_text)
        print(f"AI parsing found {len(structured_questions)} questions.")

        if not structured_questions: return 0

        # 1. Prepare all question texts first
        question_texts = [q.get("question_text", "N/A") for q in structured_questions if len(q.get("question_text", "")) > 10]
        
        # --- THE FIX IS HERE ---
        # 2. Run the heavy, synchronous embedding for all texts at once in a background thread
        print(f"Embedding {len(question_texts)} questions in a background thread...")
        all_vectors = await asyncio.to_thread(self.embedding_model.encode, question_texts)
        print("Embedding complete.")

        # 3. Now, create the database objects (this is fast)
        for i, q_data in enumerate(filter(lambda q: len(q.get("question_text", "")) > 10, structured_questions)):
            new_question = models.Question(
                question_id=str(uuid.uuid4()),
                question_text=question_texts[i],
                vector=all_vectors[i].tolist(),
                question_type=q_data.get("question_type", "MCSC"),
                source=models.SourceEnum.PYQ,
                source_details=source_name
            )
            db.add(new_question)
            
            for option_text in q_data.get("options", []):
                new_option = models.QuestionOption(
                    option_id=str(uuid.uuid4()),
                    question_id=new_question.question_id,
                    option_text=option_text
                )
                db.add(new_option)
        
        await db.commit()
        print("Database commit successful.")
        return len(question_texts)
    
    async def answer_query(self, db: AsyncSession, query: str) -> str:
        """
        Finds relevant questions using vector search and generates an answer with Gemini.
        """
        print(f"Received query: {query}")
        
        # 1. Embed the user's query
        query_vector = self.embedding_model.encode(query)

        # 2. Search the database for the most relevant questions
        print("Performing vector search in the database...")
        stmt = (
            select(models.Question)
            .options(selectinload(models.Question.options)) # Pre-load options
            .order_by(models.Question.vector.cosine_distance(query_vector))
            .limit(5) # Retrieve the top 5 most relevant questions
        )
        result = await db.execute(stmt)
        retrieved_questions = result.scalars().unique().all()

        if not retrieved_questions:
            return "I could not find any relevant questions in the database to answer your query."

        # 3. Format the retrieved questions as context for the LLM
        context_str = ""
        for i, q in enumerate(retrieved_questions):
            context_str += f"--- Question {i+1} ---\n"
            context_str += f"Question Text: {q.question_text}\n"
            context_str += "Options:\n"
            for opt in q.options:
                context_str += f"- {opt.option_text}\n"
            context_str += "\n"
        
        # 4. Create a prompt and generate an answer with Gemini
        prompt = f"""
        You are a helpful AI assistant for students preparing for JEE and NEET exams.
        Based only on the context provided below, which contains questions and options from past exams, please answer the user's query.

        CONTEXT:
        {context_str}

        QUERY:
        {query}

        ANSWER:
        """
        
        print("Sending context and query to Gemini...")
        try:
            response = await self.parser_model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            print(f"An error occurred with the Gemini API: {e}")
            return "Sorry, I was unable to generate an answer at this time."

rag_service = RAGService()