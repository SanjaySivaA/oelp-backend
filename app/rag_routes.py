# app/rag_routes.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

# Import your project's modules
from . import schemas, models
from .database import get_db
from .auth import get_current_user
from .rag_service import rag_service

# --- THIS IS THE MISSING LINE ---
# Create an instance of APIRouter
router = APIRouter(
    prefix="/rag",
    tags=["RAG System"]
)

@router.post("/upload-pdf") # Now 'router' is defined and this will work
async def upload_pdf_for_rag(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    pdf_content = await file.read()
    questions_found = await rag_service.process_and_store_pdf(db, pdf_content, file.filename)
    if questions_found > 0:
        return {"message": f"Successfully processed and stored {questions_found} questions."}
    else:
        raise HTTPException(status_code=500, detail="Failed to process or find questions in the PDF.")


@router.post("/query", response_model=schemas.RAGQueryResponse)
async def query_rag_system(
    request: schemas.RAGQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        # Call the new service method with the user's query
        answer = await rag_service.answer_query(db, request.query)
        return {"answer": answer}
    except Exception as e:
        # Log the error in a real application
        raise HTTPException(status_code=500, detail="Failed to retrieve answer.")

    # This is a placeholder for your query logic
    # Make sure your rag_service has an answer_query method if you use this
    # answer = await rag_service.answer_query(db, request.query)
    # return {"answer": answer}
    return {"answer": "Query endpoint is active but logic needs to be connected."}  