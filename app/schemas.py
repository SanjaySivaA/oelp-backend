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

class AnswerSubmission(BaseModel):
    question_id: str
    # For MCMC, multiple options can be selected
    selected_option_ids: Optional[List[str]] = None 
    integer_answer: Optional[int] = None
    time_taken_seconds: int

class TestSubmissionRequest(BaseModel):
    answers: List[AnswerSubmission]

class TestSubmissionResponse(BaseModel):
    message: str
    test_id: str
    final_score: float
    max_score: float
