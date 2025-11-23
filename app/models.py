import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    BigInteger
)
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from pgvector.sqlalchemy import Vector 

Base = declarative_base()

# -----------------------------
# --- ENUM DEFINITIONS ---
# -----------------------------

class QuestionTypeEnum(enum.Enum):
    MCSC = "MCSC"
    MCMC = "MCMC"
    NUMERICAL = "NUMERICAL"

class DifficultyLevelEnum(enum.Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    
class SourceEnum(enum.Enum):
    PYQ = "PYQ"
    NCERT = "NCERT"
    GENERATED = "GENERATED"
    COMPETITIVE_EXAM_ARCHIVE = "Competitive Exam Archive"

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

# -----------------------------
# --- TABLE DEFINITIONS ---
# -----------------------------

class User(Base):
    __tablename__ = 'users'
    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    tests: Mapped[list["Test"]] = relationship(back_populates="user")
    enrollments: Mapped[list["UserEnrollment"]] = relationship(back_populates="user")
    starred_questions: Mapped[list["UserStarredQuestion"]] = relationship(back_populates="user")
    owned_templates: Mapped[list["TestTemplate"]] = relationship(back_populates="owner")
    subject_analytics: Mapped[list["UserSubjectAnalytics"]] = relationship(back_populates="user")
    chapter_analytics: Mapped[list["UserChapterAnalytics"]] = relationship(back_populates="user")
    question_type_analytics: Mapped[list["UserQuestionTypeAnalytics"]] = relationship(back_populates="user")

class Exam(Base):
    __tablename__ = 'exams'
    exam_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exam_name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    
    test_templates: Mapped[list["TestTemplate"]] = relationship(back_populates="exam")

class UserEnrollment(Base):
    __tablename__ = 'user_enrollments'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.user_id'), primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey('exams.exam_id'), primary_key=True)

    user: Mapped["User"] = relationship(back_populates="enrollments")
    exam: Mapped["Exam"] = relationship()

class Subject(Base):
    __tablename__ = 'subjects'
    subject_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject_name: Mapped[str] = mapped_column(String, nullable=False)

    chapters: Mapped[list["Chapter"]] = relationship(back_populates="subject")
    test_templates: Mapped[list["TestTemplate"]] = relationship(back_populates="subject")

class Chapter(Base):
    __tablename__ = 'chapters'
    chapter_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chapter_name: Mapped[str] = mapped_column(String, nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey('subjects.subject_id'))

    subject: Mapped["Subject"] = relationship(back_populates="chapters")
    subtopics: Mapped[list["Subtopic"]] = relationship(back_populates="chapter")
    test_templates: Mapped[list["TestTemplate"]] = relationship(back_populates="chapter")

class Subtopic(Base):
    __tablename__ = 'subtopics'
    subtopic_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subtopic_name: Mapped[str] = mapped_column(String, nullable=False)
    chapter_id: Mapped[int] = mapped_column(ForeignKey('chapters.chapter_id'))

    chapter: Mapped["Chapter"] = relationship(back_populates="subtopics")
    questions: Mapped[list["Question"]] = relationship(back_populates="subtopic")
    source_chunks: Mapped[list["SourceMaterialChunk"]] = relationship(back_populates="subtopic")

class Question(Base):
    __tablename__ = 'questions'
    question_id: Mapped[str] = mapped_column(String, primary_key=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str] = mapped_column(String, nullable=True)
    vector = mapped_column(Vector(768), nullable=True)
    question_type: Mapped[QuestionTypeEnum] = mapped_column(Enum(QuestionTypeEnum), nullable=False)
    subtopic_id: Mapped[int] = mapped_column(ForeignKey('subtopics.subtopic_id'))
    difficulty_level: Mapped[DifficultyLevelEnum] = mapped_column(Enum(DifficultyLevelEnum))
    source: Mapped[SourceEnum] = mapped_column(Enum(SourceEnum))
    source_details: Mapped[str] = mapped_column(String, nullable=True)
    positive_marks: Mapped[int] = mapped_column(Integer, default=4)
    negative_marks: Mapped[int] = mapped_column(Integer, default=1)
    solution_explanation: Mapped[str] = mapped_column(Text, nullable=True)
    ai_validation_status: Mapped[AIValidationStatusEnum] = mapped_column(Enum(AIValidationStatusEnum), default=AIValidationStatusEnum.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    subtopic: Mapped["Subtopic"] = relationship(back_populates="questions")
    options: Mapped[list["QuestionOption"]] = relationship(back_populates="question")
    test_associations: Mapped[list["TestTemplateQuestion"]] = relationship(back_populates="question")

class QuestionOption(Base):
    __tablename__ = 'question_options'
    option_id: Mapped[str] = mapped_column(String, primary_key=True)
    question_id: Mapped[str] = mapped_column(ForeignKey('questions.question_id'))
    option_text: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str] = mapped_column(String, nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    
    question: Mapped["Question"] = relationship(back_populates="options")

class QuestionExamApplicability(Base):
    __tablename__ = 'question_exam_applicability'
    question_id: Mapped[str] = mapped_column(ForeignKey('questions.question_id'), primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey('exams.exam_id'), primary_key=True)

# --- Test Definition & Lifecycle Tables ---

class TestTemplate(Base):
    __tablename__ = 'test_templates'
    template_id: Mapped[str] = mapped_column(String, primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(ForeignKey('users.user_id'), nullable=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey('exams.exam_id'))
    subject_id: Mapped[int] = mapped_column(ForeignKey('subjects.subject_id'), nullable=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey('chapters.chapter_id'), nullable=True)
    template_name: Mapped[str] = mapped_column(String, nullable=False)
    test_type: Mapped[TestTypeEnum] = mapped_column(Enum(TestTypeEnum))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner: Mapped["User"] = relationship(back_populates="owned_templates")
    exam: Mapped["Exam"] = relationship(back_populates="test_templates")
    subject: Mapped["Subject"] = relationship(back_populates="test_templates")
    chapter: Mapped["Chapter"] = relationship(back_populates="test_templates")
    question_associations: Mapped[list["TestTemplateQuestion"]] = relationship(back_populates="template")
    attempts: Mapped[list["Test"]] = relationship(back_populates="template")

class TestTemplateQuestion(Base):
    __tablename__ = 'test_template_questions'
    template_id: Mapped[str] = mapped_column(ForeignKey('test_templates.template_id'), primary_key=True)
    question_id: Mapped[str] = mapped_column(ForeignKey('questions.question_id'), primary_key=True)
    question_order: Mapped[int] = mapped_column(Integer)

    template: Mapped["TestTemplate"] = relationship(back_populates="question_associations")
    question: Mapped["Question"] = relationship(back_populates="test_associations")

class Test(Base):
    __tablename__ = 'tests'
    test_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.user_id'))
    template_id: Mapped[str] = mapped_column(ForeignKey('test_templates.template_id'))
    
    test_name: Mapped[str] = mapped_column(String)
    test_type: Mapped[TestTypeEnum] = mapped_column(Enum(TestTypeEnum))
    
    status: Mapped[TestStatusEnum] = mapped_column(Enum(TestStatusEnum))
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    final_score: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="tests")
    template: Mapped["TestTemplate"] = relationship(back_populates="attempts")
    answers: Mapped[list["TestAnswer"]] = relationship(back_populates="test")

class TestAnswer(Base):
    __tablename__ = 'test_answers'
    answer_id: Mapped[str] = mapped_column(String, primary_key=True)
    test_id: Mapped[str] = mapped_column(ForeignKey('tests.test_id'))
    question_id: Mapped[str] = mapped_column(ForeignKey('questions.question_id'))
    integer_answer: Mapped[int] = mapped_column(Integer, nullable=True)
    status: Mapped[TestAnswerStatusEnum] = mapped_column(Enum(TestAnswerStatusEnum), default=TestAnswerStatusEnum.UNATTEMPTED)
    time_taken_seconds: Mapped[int] = mapped_column(Integer, default=0)

    test: Mapped["Test"] = relationship(back_populates="answers")
    question: Mapped["Question"] = relationship()
    selections: Mapped[list["TestAnswerSelection"]] = relationship(back_populates="test_answer")

class TestAnswerSelection(Base):
    __tablename__ = 'test_answer_selections'
    answer_id: Mapped[str] = mapped_column(ForeignKey('test_answers.answer_id'), primary_key=True)
    selected_option_id: Mapped[str] = mapped_column(ForeignKey('question_options.option_id'), primary_key=True)
    
    test_answer: Mapped["TestAnswer"] = relationship(back_populates="selections")
    selected_option: Mapped["QuestionOption"] = relationship()

# User Features & Analytics
class UserStarredQuestion(Base):
    __tablename__ = 'user_starred_questions'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.user_id'), primary_key=True)
    question_id: Mapped[str] = mapped_column(ForeignKey('questions.question_id'), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    user: Mapped["User"] = relationship(back_populates="starred_questions")
    question: Mapped["Question"] = relationship()

class UserSubjectAnalytics(Base):
    __tablename__ = 'user_subject_analytics'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.user_id'), primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey('exams.exam_id'), primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey('subjects.subject_id'), primary_key=True)
    questions_attempted: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    total_time_taken_seconds: Mapped[int] = mapped_column(BigInteger, default=0)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=lambda: datetime.now(timezone.utc), default=lambda: datetime.now(timezone.utc))
    user: Mapped["User"] = relationship(back_populates="subject_analytics")

class UserChapterAnalytics(Base):
    __tablename__ = 'user_chapter_analytics'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.user_id'), primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey('exams.exam_id'), primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey('chapters.chapter_id'), primary_key=True)
    questions_attempted: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    total_time_taken_seconds: Mapped[int] = mapped_column(BigInteger, default=0)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=lambda: datetime.now(timezone.utc), default=lambda: datetime.now(timezone.utc))
    user: Mapped["User"] = relationship(back_populates="chapter_analytics")

class UserQuestionTypeAnalytics(Base):
    __tablename__ = 'user_question_type_analytics'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.user_id'), primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey('exams.exam_id'), primary_key=True)
    question_type: Mapped[str] = mapped_column(String, primary_key=True)
    questions_attempted: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=lambda: datetime.now(timezone.utc), default=lambda: datetime.now(timezone.utc))
    user: Mapped["User"] = relationship(back_populates="question_type_analytics")

class SourceMaterialChunk(Base):
    __tablename__ = 'source_material_chunks'
    chunk_id: Mapped[str] = mapped_column(String, primary_key=True)
    subtopic_id: Mapped[int] = mapped_column(ForeignKey('subtopics.subtopic_id'), nullable=True)
    source_name: Mapped[str] = mapped_column(String)
    chunk_text: Mapped[str] = mapped_column(Text)
    vector = mapped_column(Vector(768))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    subtopic: Mapped["Subtopic"] = relationship(back_populates="source_chunks")