from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.db.models import Question, Unit, DifficultyLevel, SeniorityLevel, QuestionGroup
from fastapi import HTTPException, status

class QuestionService:
    """
    Сервіс для роботи з питаннями для співбесід
    """
    
    @staticmethod
    def get_questions(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        unit_id: Optional[int] = None,
        difficulty_id: Optional[int] = None,
        level_id: Optional[int] = None,
        group_id: Optional[int] = None,
        text_search: Optional[str] = None
    ) -> List[Question]:
        """
        Отримати список питань з можливістю фільтрації
        """
        query = db.query(Question)
        
        # Застосування фільтрів
        if unit_id:
            query = query.filter(Question.unit_id == unit_id)
        if difficulty_id:
            query = query.filter(Question.difficulty_id == difficulty_id)
        if level_id:
            query = query.filter(Question.level_id == level_id)
        if group_id:
            query = query.filter(Question.group_id == group_id)
        if text_search:
            query = query.filter(Question.text.ilike(f"%{text_search}%"))
            
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_question_by_id(db: Session, question_id: int) -> Question:
        """
        Отримати питання за ідентифікатором
        """
        question = db.query(Question).filter(Question.id == question_id).first()
        if question is None:
            raise HTTPException(status_code=404, detail="Питання не знайдено")
        return question
    
    @staticmethod
    def create_question(db: Session, question_data: Dict[str, Any]) -> Question:
        """
        Створити нове питання
        """
        db_question = Question(**question_data)
        db.add(db_question)
        db.commit()
        db.refresh(db_question)
        return db_question
    
    @staticmethod
    def update_question(db: Session, question_id: int, question_data: Dict[str, Any]) -> Question:
        """
        Оновити існуюче питання
        """
        db_question = QuestionService.get_question_by_id(db, question_id)
        
        # Оновлення тільки наданих полів
        for key, value in question_data.items():
            setattr(db_question, key, value)
        
        db.commit()
        db.refresh(db_question)
        return db_question
    
    @staticmethod
    def delete_question(db: Session, question_id: int) -> bool:
        """
        Видалити питання
        """
        db_question = QuestionService.get_question_by_id(db, question_id)
        db.delete(db_question)
        db.commit()
        return True
    
    # Методи для роботи з фільтрами (Unit, Difficulty, Level, Group)
    
    @staticmethod
    def get_units(db: Session, skip: int = 0, limit: int = 100) -> List[Unit]:
        """
        Отримати список підрозділів/проектів
        """
        return db.query(Unit).offset(skip).limit(limit).all()
    
    @staticmethod
    def create_unit(db: Session, unit_data: Dict[str, Any]) -> Unit:
        """
        Створити новий підрозділ/проект
        """
        db_unit = Unit(**unit_data)
        db.add(db_unit)
        db.commit()
        db.refresh(db_unit)
        return db_unit
    
    @staticmethod
    def get_difficulties(db: Session, skip: int = 0, limit: int = 100) -> List[DifficultyLevel]:
        """
        Отримати список рівнів складності
        """
        return db.query(DifficultyLevel).offset(skip).limit(limit).all()
    
    @staticmethod
    def create_difficulty(db: Session, difficulty_data: Dict[str, Any]) -> DifficultyLevel:
        """
        Створити новий рівень складності
        """
        db_difficulty = DifficultyLevel(**difficulty_data)
        db.add(db_difficulty)
        db.commit()
        db.refresh(db_difficulty)
        return db_difficulty
    
    @staticmethod
    def get_seniority_levels(db: Session, skip: int = 0, limit: int = 100) -> List[SeniorityLevel]:
        """
        Отримати список рівнів позиції
        """
        return db.query(SeniorityLevel).offset(skip).limit(limit).all()
    
    @staticmethod
    def create_seniority_level(db: Session, level_data: Dict[str, Any]) -> SeniorityLevel:
        """
        Створити новий рівень позиції
        """
        db_level = SeniorityLevel(**level_data)
        db.add(db_level)
        db.commit()
        db.refresh(db_level)
        return db_level
    
    @staticmethod
    def get_question_groups(db: Session, skip: int = 0, limit: int = 100) -> List[QuestionGroup]:
        """
        Отримати список груп питань
        """
        return db.query(QuestionGroup).offset(skip).limit(limit).all()
    
    @staticmethod
    def create_question_group(db: Session, group_data: Dict[str, Any]) -> QuestionGroup:
        """
        Створити нову групу питань
        """
        db_group = QuestionGroup(**group_data)
        db.add(db_group)
        db.commit()
        db.refresh(db_group)
        return db_group
