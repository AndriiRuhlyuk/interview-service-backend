from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.db.models import Question, Unit, DifficultyLevel, SeniorityLevel, QuestionGroup
from pydantic import BaseModel
import datetime

router = APIRouter(prefix="/api/questions", tags=["questions"])

# Pydantic моделі для запитів і відповідей
class QuestionBase(BaseModel):
    text: str
    weight: float = 1.0
    docs_reference: Optional[str] = None
    priority: int = 1
    unit_id: Optional[int] = None
    difficulty_id: Optional[int] = None
    level_id: Optional[int] = None
    group_id: Optional[int] = None

class QuestionCreate(QuestionBase):
    pass

class QuestionUpdate(QuestionBase):
    text: Optional[str] = None
    weight: Optional[float] = None
    docs_reference: Optional[str] = None
    priority: Optional[int] = None

class QuestionResponse(QuestionBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    
    class Config:
        orm_mode = True


# Ендпоінти для роботи з питаннями
@router.post("/", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_question(question: QuestionCreate, db: Session = Depends(get_db)):
    """Створити нове питання"""
    db_question = Question(**question.dict())
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

@router.get("/", response_model=List[QuestionResponse])
def get_questions(
    skip: int = 0, 
    limit: int = 100,
    unit_id: Optional[int] = None,
    difficulty_id: Optional[int] = None,
    level_id: Optional[int] = None,
    group_id: Optional[int] = None,
    text_search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Отримати список питань з фільтрацією"""
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

@router.get("/{question_id}", response_model=QuestionResponse)
def get_question(question_id: int, db: Session = Depends(get_db)):
    """Отримати питання за ідентифікатором"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if question is None:
        raise HTTPException(status_code=404, detail="Питання не знайдено")
    return question

@router.put("/{question_id}", response_model=QuestionResponse)
def update_question(question_id: int, question: QuestionUpdate, db: Session = Depends(get_db)):
    """Оновити питання"""
    db_question = db.query(Question).filter(Question.id == question_id).first()
    if db_question is None:
        raise HTTPException(status_code=404, detail="Питання не знайдено")
    
    # Оновлення тільки наданих полів
    update_data = question.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_question, key, value)
    
    db_question.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(db_question)
    return db_question

@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(question_id: int, db: Session = Depends(get_db)):
    """Видалити питання"""
    db_question = db.query(Question).filter(Question.id == question_id).first()
    if db_question is None:
        raise HTTPException(status_code=404, detail="Питання не знайдено")
    
    db.delete(db_question)
    db.commit()
    return {"detail": "Питання видалено успішно"}

# Додаткові моделі для фільтрів
class UnitBase(BaseModel):
    name: str
    description: Optional[str] = None

class UnitCreate(UnitBase):
    pass

class UnitResponse(UnitBase):
    id: int
    
    class Config:
        orm_mode = True

class DifficultyBase(BaseModel):
    name: str

class DifficultyCreate(DifficultyBase):
    pass

class DifficultyResponse(DifficultyBase):
    id: int
    
    class Config:
        orm_mode = True

class SeniorityBase(BaseModel):
    name: str

class SeniorityCreate(SeniorityBase):
    pass

class SeniorityResponse(SeniorityBase):
    id: int
    
    class Config:
        orm_mode = True

class QuestionGroupBase(BaseModel):
    name: str
    subject: str

class QuestionGroupCreate(QuestionGroupBase):
    pass

class QuestionGroupResponse(QuestionGroupBase):
    id: int
    
    class Config:
        orm_mode = True

# Ендпоінти для фільтрів
@router.post("/units/", response_model=UnitResponse, status_code=status.HTTP_201_CREATED)
def create_unit(unit: UnitCreate, db: Session = Depends(get_db)):
    """Створити новий підрозділ/проект"""
    db_unit = Unit(**unit.dict())
    db.add(db_unit)
    db.commit()
    db.refresh(db_unit)
    return db_unit

@router.get("/units/", response_model=List[UnitResponse])
def get_units(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Отримати список підрозділів/проектів"""
    return db.query(Unit).offset(skip).limit(limit).all()

@router.post("/difficulties/", response_model=DifficultyResponse, status_code=status.HTTP_201_CREATED)
def create_difficulty(difficulty: DifficultyCreate, db: Session = Depends(get_db)):
    """Створити новий рівень складності"""
    db_difficulty = DifficultyLevel(**difficulty.dict())
    db.add(db_difficulty)
    db.commit()
    db.refresh(db_difficulty)
    return db_difficulty

@router.get("/difficulties/", response_model=List[DifficultyResponse])
def get_difficulties(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Отримати список рівнів складності"""
    return db.query(DifficultyLevel).offset(skip).limit(limit).all()

@router.post("/seniority-levels/", response_model=SeniorityResponse, status_code=status.HTTP_201_CREATED)
def create_seniority(seniority: SeniorityCreate, db: Session = Depends(get_db)):
    """Створити новий рівень позиції"""
    db_seniority = SeniorityLevel(**seniority.dict())
    db.add(db_seniority)
    db.commit()
    db.refresh(db_seniority)
    return db_seniority

@router.get("/seniority-levels/", response_model=List[SeniorityResponse])
def get_seniority_levels(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Отримати список рівнів позиції"""
    return db.query(SeniorityLevel).offset(skip).limit(limit).all()

@router.post("/groups/", response_model=QuestionGroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(group: QuestionGroupCreate, db: Session = Depends(get_db)):
    """Створити нову групу питань"""
    db_group = QuestionGroup(**group.dict())
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

@router.get("/groups/", response_model=List[QuestionGroupResponse])
def get_groups(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Отримати список груп питань"""
    return db.query(QuestionGroup).offset(skip).limit(limit).all()
