import enum
from datetime import datetime

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Enum,
    Float,
    BigInteger,
    ForeignKey,
    Text,
    PrimaryKeyConstraint,
    UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from pgvector.sqlalchemy import Vector # For vector embeddings

Base = declarative_base()

# ----------------------------------------Enums------------------------------------------------------

class QuestionType(enum.Enum):
    MCSC = "MCSC" # Multiple Choice Single Correct
    MCMC = "MCMC" # Multiple Choice Multiple Correct
    INT = "INT"   # Integer answers
    NUM = "NUM"   # Numerical

class DifficultyLevel(enum.Enum):
    EASY = "EASY" 
    MEDIUM = "MEDIUM"
    HARD = "HARD" 

class SourceEnum(enum.Enum):
    PYQ = "PYQ" 
    NCERT = "NCERT"
    GENERATED = "GENERATED" 

class AIValidationStatusEnum(enum.Enum):
    PENDING = "PENDING"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"

class TestTypeEnum(enum.Enum):
    CHAPTER_TEST = "CHAPTER_TEST"
    SUBJECT_TEST = "SUBJECT_TEST"
    FULL_MOCK = "FULL_MOCK"
    CUSTOM = "CUSTOM"

class TestStatusEnum(enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"

class TestAnswerStatusEnum(enum.Enum):
    CORRECT = "CORRECT"
    INCORRECT = "INCORRECT"
    UNATTEMPTED = "UNATTEMPTED"
    MARKED_FOR_REVIEW = "MARKED_FOR_REVIEW"

# ----------------------------------------Tables------------------------------------------------------

class User(Base):
    __tablename__ = 'users'
    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    tests: Mapped[list["Test"]] = relationship(back_populates="user")
    enrollments: Mapped[list["UserEnrollment"]] = relationship(back_populates="user")
    starred_questions: Mapped[list["UserStarredQuestion"]] = relationship(back_populates="user")
    subject_analytics: Mapped[list["UserSubjectAnalytics"]] = relationship(back_populates="user")
    chapter_analytics: Mapped[list["UserChapterAnalytics"]] = relationship(back_populates="user")
    question_type_analytics: Mapped[list["UserQuestionTypeAnalytics"]] = relationship(back_populates="user")

class Exam(Base):
    __tablename__ = 'exams'
    exam_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exam_name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    # Relationships
    enrollments: Mapped[list["UserEnrollment"]] = relationship(back_populates="exam")
    question_applicability: Mapped[list["QuestionExamApplicability"]] = relationship(back_populates="exam")


class UserEnrollment(Base):
    __tablename__ = 'user_enrollments'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.user_id'), primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey('exams.exam_id'), primary_key=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="enrollments")
    exam: Mapped["Exam"] = relationship(back_populates="enrollments")


# Content Hierarchy & Definitions
class Subject(Base):
    __tablename__ = 'subjects'
    subject_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject_name: Mapped[str] = mapped_column(String, nullable=False)

    # Relationships
    chapters: Mapped[list["Chapter"]] = relationship(back_populates="subject")
    tests: Mapped[list["Test"]] = relationship(back_populates="subject")

class Chapter(Base):
    __tablename__ = 'chapters'
    chapter_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chapter_name: Mapped[str] = mapped_column(String, nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey('subjects.subject_id'))

    # Relationships
    subject: Mapped["Subject"] = relationship(back_populates="chapters")
    subtopics: Mapped[list["Subtopic"]] = relationship(back_populates="chapter")
    tests: Mapped[list["Test"]] = relationship(back_populates="chapter")


class Subtopic(Base):
    __tablename__ = 'subtopics'
    subtopic_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subtopic_name: Mapped[str] = mapped_column(String, nullable=False)
    chapter_id: Mapped[int] = mapped_column(ForeignKey('chapters.chapter_id'))

    # Relationships
    chapter: Mapped["Chapter"] = relationship(back_populates="subtopics")
    questions: Mapped[list["Question"]] = relationship(back_populates="subtopic")
    source_chunks: Mapped[list["SourceMaterialChunk"]] = relationship(back_populates="subtopic")

class Question(Base):
    __tablename__ = 'questions'
    question_id: Mapped[str] = mapped_column(String, primary_key=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str] = mapped_column(String, nullable=True)
    vector = mapped_column(Vector(768), nullable=True) # Assuming 768 dimensions
    question_type: Mapped[QuestionType] = mapped_column(Enum(QuestionType), nullable=False)
    subtopic_id: Mapped[int] = mapped_column(ForeignKey('subtopics.subtopic_id'))
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(Enum(DifficultyLevel))
    source: Mapped[SourceEnum] = mapped_column(Enum(SourceEnum))
    source_details: Mapped[str] = mapped_column(String, nullable=True)
    positive_marks: Mapped[int] = mapped_column(Integer, default=4)
    negative_marks: Mapped[int] = mapped_column(Integer, default=1) # Note: can be 0
    solution_explanation: Mapped[str] = mapped_column(Text, nullable=True)
    ai_validation_status: Mapped[AIValidationStatusEnum] = mapped_column(Enum(AIValidationStatusEnum), default=AIValidationStatusEnum.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    subtopic: Mapped["Subtopic"] = relationship(back_populates="questions")
    options: Mapped[list["QuestionOption"]] = relationship(back_populates="question")
    exam_applicability: Mapped[list["QuestionExamApplicability"]] = relationship(back_populates="question")


class QuestionOption(Base):
    __tablename__ = 'question_options'
    option_id: Mapped[str] = mapped_column(String, primary_key=True)
    question_id: Mapped[str] = mapped_column(ForeignKey('questions.question_id'))
    option_text: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str] = mapped_column(String, nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    question: Mapped["Question"] = relationship(back_populates="options")

class QuestionExamApplicability(Base):
    __tablename__ = 'question_exam_applicability'
    question_id: Mapped[str] = mapped_column(ForeignKey('questions.question_id'), primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey('exams.exam_id'), primary_key=True)

    # Relationships
    question: Mapped["Question"] = relationship(back_populates="exam_applicability")
    exam: Mapped["Exam"] = relationship(back_populates="question_applicability")


# Test Attempt Lifecycle
class Test(Base):
    __tablename__ = 'tests'
    test_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.user_id'))
    chapter_id: Mapped[int] = mapped_column(ForeignKey('chapters.chapter_id'), nullable=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey('subjects.subject_id'), nullable=True)
    test_name: Mapped[str] = mapped_column(String)
    test_type: Mapped[TestTypeEnum] = mapped_column(Enum(TestTypeEnum))
    status: Mapped[TestStatusEnum] = mapped_column(Enum(TestStatusEnum))
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    final_score: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="tests")
    chapter: Mapped["Chapter"] = relationship(back_populates="tests")
    subject: Mapped["Subject"] = relationship(back_populates="tests")
    answers: Mapped[list["TestAnswer"]] = relationship(back_populates="test")

class TestAnswer(Base):
    __tablename__ = 'test_answers'
    answer_id: Mapped[str] = mapped_column(String, primary_key=True)
    test_id: Mapped[str] = mapped_column(ForeignKey('tests.test_id'))
    question_id: Mapped[str] = mapped_column(ForeignKey('questions.question_id'))
    integer_answer: Mapped[int] = mapped_column(Integer, nullable=True)
    status: Mapped[TestAnswerStatusEnum] = mapped_column(Enum(TestAnswerStatusEnum), default=TestAnswerStatusEnum.UNATTEMPTED)
    time_taken_seconds: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    test: Mapped["Test"] = relationship(back_populates="answers")
    question: Mapped["Question"] = relationship()
    selections: Mapped[list["TestAnswerSelection"]] = relationship(back_populates="test_answer")

class TestAnswerSelection(Base):
    __tablename__ = 'test_answer_selections'
    answer_id: Mapped[str] = mapped_column(ForeignKey('test_answers.answer_id'), primary_key=True)
    selected_option_id: Mapped[str] = mapped_column(ForeignKey('question_options.option_id'), primary_key=True)
    
    # Relationships
    test_answer: Mapped["TestAnswer"] = relationship(back_populates="selections")
    selected_option: Mapped["QuestionOption"] = relationship()

# User Features
class UserStarredQuestion(Base):
    __tablename__ = 'user_starred_questions'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.user_id'), primary_key=True)
    question_id: Mapped[str] = mapped_column(ForeignKey('questions.question_id'), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="starred_questions")
    question: Mapped["Question"] = relationship()


# Analytics Aggregate Tables
class UserSubjectAnalytics(Base):
    __tablename__ = 'user_subject_analytics'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.user_id'), primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey('exams.exam_id'), primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey('subjects.subject_id'), primary_key=True)
    questions_attempted: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    total_time_taken_seconds: Mapped[int] = mapped_column(BigInteger, default=0) # Using BigInteger for safety
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=datetime.utcnow, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="subject_analytics")

class UserChapterAnalytics(Base):
    __tablename__ = 'user_chapter_analytics'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.user_id'), primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey('exams.exam_id'), primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey('chapters.chapter_id'), primary_key=True)
    questions_attempted: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    total_time_taken_seconds: Mapped[int] = mapped_column(BigInteger, default=0)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=datetime.utcnow, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="chapter_analytics")

class UserQuestionTypeAnalytics(Base):
    __tablename__ = 'user_question_type_analytics'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.user_id'), primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey('exams.exam_id'), primary_key=True)
    question_type: Mapped[str] = mapped_column(String, primary_key=True) # Storing enum name as string
    questions_attempted: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=datetime.utcnow, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="question_type_analytics")

# AI & RAG Support Tables
class SourceMaterialChunk(Base):
    __tablename__ = 'source_material_chunks'
    chunk_id: Mapped[str] = mapped_column(String, primary_key=True)
    subtopic_id: Mapped[int] = mapped_column(ForeignKey('subtopics.subtopic_id'), nullable=True)
    source_name: Mapped[str] = mapped_column(String)
    chunk_text: Mapped[str] = mapped_column(Text)
    vector = mapped_column(Vector(768)) # Assuming 768 dimensions
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    subtopic: Mapped["Subtopic"] = relationship(back_populates="source_chunks")