from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.db.models import ApplicationTemplate, Question, QuestionList
from pydantic import BaseModel
import datetime

router = APIRouter(prefix="/api/templates", tags=["templates"])

# Pydantic моделі для запитів і відповідей
class TemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    position: str

class TemplateCreate(TemplateBase):
    pass

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    position: Optional[str] = None

class QuestionInTemplate(BaseModel):
    id: int

class TemplateQuestionsList(BaseModel):
    template_id: int
    questions: List[int]  # список ідентифікаторів питань

class TemplateResponse(TemplateBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    
    class Config:
        orm_mode = True

class TemplateDetailResponse(TemplateResponse):
    questions: List[int] = []  # список ідентифікаторів питань
    
    class Config:
        orm_mode = True

# Ендпоінти для роботи з шаблонами
@router.post("/", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(template: TemplateCreate, db: Session = Depends(get_db)):
    """Створити новий шаблон"""
    db_template = ApplicationTemplate(**template.dict())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.get("/", response_model=List[TemplateResponse])
def get_templates(
    skip: int = 0, 
    limit: int = 100,
    position: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Отримати список шаблонів з фільтрацією"""
    query = db.query(ApplicationTemplate)
    
    # Застосування фільтрів
    if position:
        query = query.filter(ApplicationTemplate.position.ilike(f"%{position}%"))
        
    return query.offset(skip).limit(limit).all()

@router.get("/{template_id}", response_model=TemplateDetailResponse)
def get_template(template_id: int, db: Session = Depends(get_db)):
    """Отримати шаблон за ідентифікатором з питаннями"""
    template = db.query(ApplicationTemplate).filter(ApplicationTemplate.id == template_id).first()
    if template is None:
        raise HTTPException(status_code=404, detail="Шаблон не знайдено")
    
    # Додати список ідентифікаторів питань
    result = TemplateDetailResponse.from_orm(template)
    result.questions = [q.id for q in template.questions]
    return result

@router.put("/{template_id}", response_model=TemplateResponse)
def update_template(template_id: int, template: TemplateUpdate, db: Session = Depends(get_db)):
    """Оновити шаблон"""
    db_template = db.query(ApplicationTemplate).filter(ApplicationTemplate.id == template_id).first()
    if db_template is None:
        raise HTTPException(status_code=404, detail="Шаблон не знайдено")
    
    # Оновлення тільки наданих полів
    update_data = template.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_template, key, value)
    
    db_template.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(db_template)
    return db_template

@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(template_id: int, db: Session = Depends(get_db)):
    """Видалити шаблон"""
    db_template = db.query(ApplicationTemplate).filter(ApplicationTemplate.id == template_id).first()
    if db_template is None:
        raise HTTPException(status_code=404, detail="Шаблон не знайдено")
    
    db.delete(db_template)
    db.commit()
    return {"detail": "Шаблон видалено успішно"}

@router.post("/{template_id}/questions", response_model=TemplateDetailResponse)
def add_questions_to_template(template_id: int, questions_list: TemplateQuestionsList, db: Session = Depends(get_db)):
    """Додати питання до шаблону"""
    db_template = db.query(ApplicationTemplate).filter(ApplicationTemplate.id == template_id).first()
    if db_template is None:
        raise HTTPException(status_code=404, detail="Шаблон не знайдено")
    
    # Перевірка існування питань і додавання їх до шаблону
    for question_id in questions_list.questions:
        question = db.query(Question).filter(Question.id == question_id).first()
        if question is None:
            raise HTTPException(status_code=404, detail=f"Питання з ID {question_id} не знайдено")
        db_template.questions.append(question)
    
    db.commit()
    db.refresh(db_template)
    
    # Підготувати відповідь
    result = TemplateDetailResponse.from_orm(db_template)
    result.questions = [q.id for q in db_template.questions]
    return result

@router.delete("/{template_id}/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_question_from_template(template_id: int, question_id: int, db: Session = Depends(get_db)):
    """Видалити питання з шаблону"""
    db_template = db.query(ApplicationTemplate).filter(ApplicationTemplate.id == template_id).first()
    if db_template is None:
        raise HTTPException(status_code=404, detail="Шаблон не знайдено")
    
    question = db.query(Question).filter(Question.id == question_id).first()
    if question is None:
        raise HTTPException(status_code=404, detail=f"Питання з ID {question_id} не знайдено")
    
    if question not in db_template.questions:
        raise HTTPException(status_code=404, detail=f"Питання з ID {question_id} не знайдено в цьому шаблоні")
    
    db_template.questions.remove(question)
    db.commit()
    
    return {"detail": "Питання видалено з шаблону успішно"}

@router.post("/{template_id}/clone", response_model=TemplateResponse)
def clone_template(template_id: int, template_data: TemplateCreate, db: Session = Depends(get_db)):
    """Клонувати шаблон з новим іменем та позицією"""
    source_template = db.query(ApplicationTemplate).filter(ApplicationTemplate.id == template_id).first()
    if source_template is None:
        raise HTTPException(status_code=404, detail="Шаблон для клонування не знайдено")
    
    # Створення нового шаблону
    new_template = ApplicationTemplate(**template_data.dict())
    db.add(new_template)
    db.flush()
    
    # Копіювання питань зі старого шаблону
    for question in source_template.questions:
        new_template.questions.append(question)
    
    db.commit()
    db.refresh(new_template)
    return new_template
