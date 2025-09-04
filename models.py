from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Boolean, Float, Text
from sqlalchemy.orm import relationship, declarative_base

from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    user_id = Column(String,primary_key=True)
    email = Column(String,unique=True,nullable=False)
    password_hash = Column(String,nullable=False)
    name = Column(String,nullable=False)
    created_at = Column(DateTime,default=datetime.utcnow)

    tests = relationship("Test",back_populates="user")
    enrollments = relationship("UserEnrollment",back_populates="user")

class Exam(Base):
    __tablename__ = "exams"
    exam_id = Column(Integer,primary_key=True)
    exam_name = Column(String,unique=True,nullable=False)

    enrollments = relationship("UserEnrollment",back_populates="exam")
    question_applicability = relationship("QuestionExamApplicability",back_populates="exam")

class UserEnrollment(Base):
    __tablename__ = "user_enrollments"
    user_id = Column(String,ForeignKey("users.user_id"),primary_key=True)
    exam_id = Column(Integer,ForeignKey("exams.exam_id"),primary_key=True)

    user = relationship("User",back_populates="enrollments")
    exam = relationship("Exam",back_populates="enrollments")

class Subject(Base):
    __tablename__ = "subjects"
    subject_id = Column(Integer,primary_key=True)
    subject_name = Column(String,nullable=False)

    chapters = relationship("Chapter",back_populates="subject")

class Chapter(Base):
    __tablename__ = "chapters"
    chapter_id = Column(Integer,primary_key=True)
    chapter_name = Column(String,nullable=False)
    subject_id = Column(Integer,ForeignKey("subjects.subject_id"))

    subject = relationship("Subject",back_populates="chapter")
    subtopic = relationship("Subtopic",back_populates="chapter")

class Subtopic(Base):
    __tablename__ = "subtopics"
    subtopic_id = Column(Integer,primary_key=True)
    subtopic_name = Column(String,nullable=False)
    chapter_id = Column(Integer,ForeignKey("chapters.chapter_id"))

    questions = relationship("Question",back_populates="subtopic")
    subtopic = relationship("Chapter",back_populates="subtopic")

