from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserPublic(BaseModel):
    user_id: str
    email: EmailStr
    name: str

    class Config:
        from_attributes = True 

# Schema for the JWT token response
class Token(BaseModel):
    access_token: str
    token_type: str

# Schema for the data embedded within the JWT
class TokenData(BaseModel):
    email: str | None = None

class RegisterResponse(BaseModel):
    user_info: UserPublic  # This key will contain a UserPublic object
    token: Token

# RAG Schemas

class RAGQueryRequest(BaseModel):
    query: str
    # subject: str | None = None # Optional subject filter
    # chapter: str | None = None # Optional chapter filter
    # subtopic: str | None = None # Optional subtopic filter

class RAGQueryResponse(BaseModel):
    answer: str

class PDFUploadResponse(BaseModel):
    message: str
    questions_found: int
    # subtopic_id: int



# --- Schemas for Analytics Endpoint ---

class StatsCardData(BaseModel):
    title: str
    value: str
    change: Optional[str] = None # Change might not always be available
    trend_color: str # 'green' or 'red'

class ChartSpot(BaseModel):
    x: float
    y: float

class TestScoreProgressionData(BaseModel):
    spots: List[ChartSpot]
    dates: List[str]
    
class SubjectPerformanceData(BaseModel):
    subject_name: str
    accuracy: float # A value between 0 and 100

class RecentTestData(BaseModel):
    test_id: str
    name: str
    subject: str
    score: int
    max_score: int
    status: str
    date: str
    time: str

class AnalyticsResponse(BaseModel):
    username: str
    stats_cards: List[StatsCardData]
    test_score_progression: TestScoreProgressionData
    subject_performance: List[SubjectPerformanceData]
    recent_tests: List[RecentTestData]

# --- Schemas for Test Submission Endpoint ---

class TestSubmissionAnswer(BaseModel):
    questionId: str
    selectedOptionIds: List[str] = [] # Used for MCSC / MCMC
    integerAnswer: int | None = None  # NEW: Used for NUMERICAL

class TestSubmissionRequest(BaseModel):
    sessionId: str
    answers: List[TestSubmissionAnswer]

class TestSubmissionResponse(BaseModel):
    message: str
    testId: str
    finalScore: float
    maxScore: float

# --- NEW: Schema for the request to start a new test ---
class StartTestRequest(BaseModel):
    subject_id: int
    test_name: str
    question_count: int = 5 # Default to 5 questions, can be overridden

# --- NEW: Schemas to structure the response to match the frontend's models ---
# These mirror your test_models.dart file.
class QuestionOptionResponse(BaseModel):
    optionId: str
    optionText: str

class QuestionResponse(BaseModel):
    questionId: str
    questionText: str
    options: List[QuestionOptionResponse]
    positiveMarks: int
    negativeMarks: int

class SectionResponse(BaseModel):
    sectionId: str
    sectionName: str
    questionType: str # "MCSC", "MCMC", "NUMERICAL", etc.
    questions: List[QuestionResponse]

class TestResponse(BaseModel):
    sessionId: str # This will be our new Test ID from the database
    testId: str    # We can reuse the sessionId here for simplicity
    testName: str
    durationInSeconds: int
    sections: List[SectionResponse]


# Response for the Chapter List screen
class ChapterCard(BaseModel):
    chapterId: int
    chapterName: str
    questionCount: int

# Request payload when clicking a Chapter Card
class StartChapterTestRequest(BaseModel):
    chapterId: int
    questionCount: int = 20 # Default to 20

class StartSubjectTestRequest(BaseModel):
    subjectId: int
    questionCount: int = 30 # Default to 30 for a subject test