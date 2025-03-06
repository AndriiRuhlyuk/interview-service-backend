from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Table, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

# Асоціативна таблиця для зв'язку багато-до-багатьох між шаблонами та питаннями
template_questions = Table(
    'template_questions',
    Base.metadata,
    Column('template_id', Integer, ForeignKey('application_templates.id'), primary_key=True),
    Column('question_id', Integer, ForeignKey('questions.id'), primary_key=True),
)

# Асоціативна таблиця для зв'язку інтерв'юерів та форм
interviewer_forms = Table(
    'interviewer_forms',
    Base.metadata,
    Column('interviewer_id', Integer, ForeignKey('interviewers.id'), primary_key=True),
    Column('form_id', Integer, ForeignKey('interview_forms.id'), primary_key=True),
)

class Unit(Base):
    """Підрозділ або проект, для якого проводиться співбесіда"""
    __tablename__ = 'units'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # Відношення
    questions = relationship("Question", back_populates="unit")
    question_lists = relationship("QuestionList", back_populates="unit")

class DifficultyLevel(Base):
    """Рівень складності питання"""
    __tablename__ = 'difficulty_levels'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)  # easy, medium, hard
    
    # Відношення
    questions = relationship("Question", back_populates="difficulty")

class SeniorityLevel(Base):
    """Рівень позиції (Junior, Middle, Senior, etc.)"""
    __tablename__ = 'seniority_levels'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)  # Junior, Middle, Senior, TeamLead, etc.
    
    # Відношення
    questions = relationship("Question", back_populates="level")

class QuestionGroup(Base):
    """Група питань за предметом/темою"""
    __tablename__ = 'question_groups'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    subject = Column(String(100), nullable=False)
    
    # Відношення
    questions = relationship("Question", back_populates="group")

class Question(Base):
    """Питання для співбесіди"""
    __tablename__ = 'questions'
    
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    weight = Column(Float, default=1.0, nullable=False)
    docs_reference = Column(Text, nullable=True)
    priority = Column(Integer, default=1, nullable=False)
    
    # Зовнішні ключі
    unit_id = Column(Integer, ForeignKey('units.id'), nullable=True)
    difficulty_id = Column(Integer, ForeignKey('difficulty_levels.id'), nullable=True)
    level_id = Column(Integer, ForeignKey('seniority_levels.id'), nullable=True)
    group_id = Column(Integer, ForeignKey('question_groups.id'), nullable=True)
    
    # Відношення
    unit = relationship("Unit", back_populates="questions")
    difficulty = relationship("DifficultyLevel", back_populates="questions")
    level = relationship("SeniorityLevel", back_populates="questions")
    group = relationship("QuestionGroup", back_populates="questions")
    templates = relationship("ApplicationTemplate", secondary=template_questions, back_populates="questions")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class ApplicationTemplate(Base):
    """Шаблон форми для співбесіди"""
    __tablename__ = 'application_templates'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    position = Column(String(100), nullable=False)  # React Engineer, Golang Engineer, etc.
    
    # Відношення
    questions = relationship("Question", secondary=template_questions, back_populates="templates")
    question_lists = relationship("QuestionList", back_populates="template")
    interview_forms = relationship("InterviewForm", back_populates="template")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class QuestionList(Base):
    """Список питань у шаблоні"""
    __tablename__ = 'question_lists'
    
    id = Column(Integer, primary_key=True)
    
    # Зовнішні ключі
    template_id = Column(Integer, ForeignKey('application_templates.id'), nullable=False)
    unit_id = Column(Integer, ForeignKey('units.id'), nullable=True)
    
    # Відношення
    template = relationship("ApplicationTemplate", back_populates="question_lists")
    unit = relationship("Unit", back_populates="question_lists")

class Interviewer(Base):
    """Співробітник, який проводить співбесіду"""
    __tablename__ = 'interviewers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    position = Column(String(100), nullable=True)
    
    # Відношення
    interview_forms = relationship("InterviewForm", secondary=interviewer_forms, back_populates="interviewers")
    scores = relationship("Score", back_populates="interviewer")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class InterviewForm(Base):
    """Форма для проведення співбесіди з конкретним кандидатом"""
    __tablename__ = 'interview_forms'
    
    id = Column(Integer, primary_key=True)
    candidate_id = Column(String(100), nullable=False)  # ID кандидата з PeopleForce
    candidate_name = Column(String(100), nullable=False)
    position = Column(String(100), nullable=False)
    interview_date = Column(DateTime, nullable=False)
    
    # Зовнішні ключі
    template_id = Column(Integer, ForeignKey('application_templates.id'), nullable=False)
    
    # Відношення
    template = relationship("ApplicationTemplate", back_populates="interview_forms")
    interviewers = relationship("Interviewer", secondary=interviewer_forms, back_populates="interview_forms")
    scores = relationship("Score", back_populates="interview_form")
    evaluations = relationship("Evaluation", back_populates="interview_form")
    feedback = relationship("Feedback", back_populates="interview_form", uselist=False)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Score(Base):
    """Оцінка на питання від інтерв'юера"""
    __tablename__ = 'scores'
    
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    value = Column(Float, nullable=False)  # Числова оцінка
    comment = Column(Text, nullable=True)
    
    # Зовнішні ключі
    interviewer_id = Column(Integer, ForeignKey('interviewers.id'), nullable=False)
    interview_form_id = Column(Integer, ForeignKey('interview_forms.id'), nullable=False)
    evaluation_id = Column(Integer, ForeignKey('evaluations.id'), nullable=True)
    
    # Відношення
    interviewer = relationship("Interviewer", back_populates="scores")
    interview_form = relationship("InterviewForm", back_populates="scores")
    evaluation = relationship("Evaluation", back_populates="scores")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Evaluation(Base):
    """Загальна оцінка кандидата"""
    __tablename__ = 'evaluations'
    
    id = Column(Integer, primary_key=True)
    total_score = Column(Float, nullable=False)
    passed = Column(Boolean, default=False)
    minimal_rate = Column(Float, nullable=False)  # Мінімально необхідне значення для проходження
    
    # Зовнішні ключі
    interview_form_id = Column(Integer, ForeignKey('interview_forms.id'), nullable=False)
    
    # Відношення
    interview_form = relationship("InterviewForm", back_populates="evaluations")
    scores = relationship("Score", back_populates="evaluation")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Feedback(Base):
    """Відгук про кандидата"""
    __tablename__ = 'feedbacks'
    
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    
    # Зовнішні ключі
    interview_form_id = Column(Integer, ForeignKey('interview_forms.id'), nullable=False)
    
    # Відношення
    interview_form = relationship("InterviewForm", back_populates="feedback")
    phrases = relationship("PredefinedPhrase", back_populates="feedback")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class PredefinedPhrase(Base):
    """Заготовлені фрази для відгуків"""
    __tablename__ = 'predefined_phrases'
    
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    category = Column(String(50), nullable=True)  # positive, negative, neutral
    
    # Зовнішні ключі
    feedback_id = Column(Integer, ForeignKey('feedbacks.id'), nullable=True)
    
    # Відношення
    feedback = relationship("Feedback", back_populates="phrases")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
