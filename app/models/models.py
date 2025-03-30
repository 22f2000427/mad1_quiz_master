from sqlite3 import Date
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, DateTime, Date
from datetime import datetime
from sqlalchemy.orm import relationship
from flask_login import UserMixin

db = SQLAlchemy()


class Users(db.Model, UserMixin):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)
    full_name = Column(String(100), nullable=False) 
    dob = Column(Date, nullable=False) 
    qualification = Column(String(50))
    
    

    
    created_quizzes = relationship("Quizzes", back_populates="creator", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempts", back_populates="user", cascade="all, delete-orphan")



class Subjects(db.Model):
    __tablename__ = 'Subjects'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)

    
    chapters = relationship("Chapters", back_populates="subject", cascade="all, delete-orphan")



class Chapters(db.Model):
    __tablename__ = 'Chapters'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    subject_id = Column(Integer, ForeignKey('Subjects.id'), nullable=False)
    description = Column(Text)

    
    subject = relationship("Subjects", back_populates="chapters")
    quizzes = relationship("Quizzes", back_populates="chapter", cascade="all, delete-orphan")



class Quizzes(db.Model):
    __tablename__ = 'Quizzes'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    chapter_id = Column(Integer, ForeignKey('Chapters.id'), nullable=False)
    difficulty = Column(String(20), nullable=True)
    scheduled_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    duration = Column(String(10), nullable=False)  # hh:mm format
    creator_id = Column(Integer, ForeignKey('Users.id'), nullable=False)

    
    chapter = relationship("Chapters", back_populates="quizzes")
    creator = relationship("Users", back_populates="created_quizzes")
    questions = relationship("Questions", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempts", back_populates="quiz", cascade="all, delete-orphan")



class Questions(db.Model):
    __tablename__ = 'Questions'
    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey('Quizzes.id'), nullable=False)
    text = Column(Text, nullable=False)

    
    quiz = relationship("Quizzes", back_populates="questions")
    options = relationship("Options", back_populates="question", cascade="all, delete-orphan")



class Options(db.Model):
    __tablename__ = 'Options'
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('Questions.id'), nullable=False)
    text = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=False, default=False)

    
    question = relationship("Questions", back_populates="options")


class QuizAttempts(db.Model):
    __tablename__ = 'QuizAttempts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('Users.id'), nullable=False)
    quiz_id = Column(Integer, ForeignKey('Quizzes.id'), nullable=False)
    score = Column(Integer, nullable=False)
    date_attempted = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("Users", back_populates="quiz_attempts")
    quiz = relationship("Quizzes", back_populates="attempts")


  
