from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.db.models import ApplicationTemplate, Question
from fastapi import HTTPException, status

class TemplateService:
    """
    Сервіс для роботи з шаблонами форм співбесід
    """
    
    @staticmethod
    def get_templates(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        position: Optional[str] = None
    ) -> List[ApplicationTemplate]:
        """
        Отримати список шаблонів з можливістю фільтрації
        """
        query = db.query(ApplicationTemplate)
        
        # Застосування фільтрів
        if position:
            query = query.filter(ApplicationTemplate.position.ilike(f"%{position}%"))
            
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_template_by_id(db: Session, template_id: int) -> ApplicationTemplate:
        """
        Отримати шаблон за ідентифікатором
        """
        template = db.query(ApplicationTemplate).filter(ApplicationTemplate.id == template_id).first()
        if template is None:
            raise HTTPException(status_code=404, detail="Шаблон не знайдено")
        return template
    
    @staticmethod
    def create_template(db: Session, template_data: Dict[str, Any]) -> ApplicationTemplate:
        """
        Створити новий шаблон
        """
        db_template = ApplicationTemplate(**template_data)
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        return db_template
    
    @staticmethod
    def update_template(db: Session, template_id: int, template_data: Dict[str, Any]) -> ApplicationTemplate:
        """
        Оновити існуючий шаблон
        """
        db_template = TemplateService.get_template_by_id(db, template_id)
        
        # Оновлення тільки наданих полів
        for key, value in template_data.items():
            setattr(db_template, key, value)
        
        db.commit()
        db.refresh(db_template)
        return db_template
    
    @staticmethod
    def delete_template(db: Session, template_id: int) -> bool:
        """
        Видалити шаблон
        """
        db_template = TemplateService.get_template_by_id(db, template_id)
        db.delete(db_template)
        db.commit()
        return True
    
    @staticmethod
    def add_questions_to_template(db: Session, template_id: int, question_ids: List[int]) -> ApplicationTemplate:
        """
        Додати питання до шаблону
        """
        db_template = TemplateService.get_template_by_id(db, template_id)
        
        # Перевірка існування питань
        for question_id in question_ids:
            question = db.query(Question).filter(Question.id == question_id).first()
            if question is None:
                raise HTTPException(status_code=404, detail=f"Питання з ID {question_id} не знайдено")
            db_template.questions.append(question)
        
        db.commit()
        db.refresh(db_template)
        return db_template
    
    @staticmethod
    def remove_question_from_template(db: Session, template_id: int, question_id: int) -> bool:
        """
        Видалити питання з шаблону
        """
        db_template = TemplateService.get_template_by_id(db, template_id)
        question = db.query(Question).filter(Question.id == question_id).first()
        
        if question is None:
            raise HTTPException(status_code=404, detail=f"Питання з ID {question_id} не знайдено")
        
        if question not in db_template.questions:
            raise HTTPException(status_code=404, detail=f"Питання з ID {question_id} не знайдено в цьому шаблоні")
        
        db_template.questions.remove(question)
        db.commit()
        return True
    
    @staticmethod
    def clone_template(db: Session, template_id: int, new_template_data: Dict[str, Any]) -> ApplicationTemplate:
        """
        Клонувати шаблон з новим іменем та позицією
        """
        source_template = TemplateService.get_template_by_id(db, template_id)
        
        # Створення нового шаблону
        new_template = ApplicationTemplate(**new_template_data)
        db.add(new_template)
        db.flush()
        
        # Копіювання питань зі старого шаблону
        for question in source_template.questions:
            new_template.questions.append(question)
        
        db.commit()
        db.refresh(new_template)
        return new_template
