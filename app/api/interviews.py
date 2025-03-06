from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.db.models import InterviewForm, ApplicationTemplate, Interviewer, Score, Evaluation, Feedback, PredefinedPhrase, Question
from pydantic import BaseModel
import datetime

router = APIRouter(prefix="/api/interviews", tags=["interviews"])

# Pydantic моделі для запитів і відповідей
class InterviewFormBase(BaseModel):
    candidate_id: str
    candidate_name: str
    position: str
    interview_date: datetime.datetime
    template_id: int

class InterviewFormCreate(InterviewFormBase):
    interviewer_ids: List[int] = []

class InterviewFormUpdate(BaseModel):
    candidate_name: Optional[str] = None
    position: Optional[str] = None
    interview_date: Optional[datetime.datetime] = None

class InterviewerBase(BaseModel):
    name: str
    email: str
    position: Optional[str] = None

class InterviewerCreate(InterviewerBase):
    pass

class InterviewerResponse(InterviewerBase):
    id: int
    
    class Config:
        orm_mode = True

class ScoreBase(BaseModel):
    question_id: int
    value: float
    comment: Optional[str] = None

class ScoreCreate(ScoreBase):
    interviewer_id: int

class ScoreResponse(ScoreBase):
    id: int
    interviewer_id: int
    
    class Config:
        orm_mode = True

class EvaluationBase(BaseModel):
    total_score: float
    passed: bool
    minimal_rate: float

class EvaluationCreate(EvaluationBase):
    pass

class EvaluationResponse(EvaluationBase):
    id: int
    
    class Config:
        orm_mode = True

class FeedbackBase(BaseModel):
    text: str

class FeedbackCreate(FeedbackBase):
    predefined_phrase_ids: List[int] = []

class FeedbackResponse(FeedbackBase):
    id: int
    
    class Config:
        orm_mode = True

class PredefinedPhraseBase(BaseModel):
    text: str
    category: Optional[str] = None

class PredefinedPhraseCreate(PredefinedPhraseBase):
    pass

class PredefinedPhraseResponse(PredefinedPhraseBase):
    id: int
    
    class Config:
        orm_mode = True

class InterviewFormResponse(InterviewFormBase):
    id: int
    interviewers: List[InterviewerResponse] = []
    
    class Config:
        orm_mode = True

class InterviewFormDetailResponse(InterviewFormResponse):
    scores: List[ScoreResponse] = []
    evaluations: List[EvaluationResponse] = []
    feedback: Optional[FeedbackResponse] = None
    
    class Config:
        orm_mode = True


# Ендпоінти для роботи з формами інтерв'ю
@router.post("/", response_model=InterviewFormResponse, status_code=status.HTTP_201_CREATED)
def create_interview_form(form: InterviewFormCreate, db: Session = Depends(get_db)):
    """Створити нову форму інтерв'ю"""
    # Перевірка існування шаблону
    template = db.query(ApplicationTemplate).filter(ApplicationTemplate.id == form.template_id).first()
    if template is None:
        raise HTTPException(status_code=404, detail="Шаблон не знайдено")
    
    # Перевірка інтерв'юерів
    interviewers = []
    for interviewer_id in form.interviewer_ids:
        interviewer = db.query(Interviewer).filter(Interviewer.id == interviewer_id).first()
        if interviewer is None:
            raise HTTPException(status_code=404, detail=f"Інтерв'юера з ID {interviewer_id} не знайдено")
        interviewers.append(interviewer)
    
    # Створення форми інтерв'ю
    db_form = InterviewForm(
        candidate_id=form.candidate_id,
        candidate_name=form.candidate_name,
        position=form.position,
        interview_date=form.interview_date,
        template_id=form.template_id
    )
    
    # Додавання інтерв'юерів
    for interviewer in interviewers:
        db_form.interviewers.append(interviewer)
    
    db.add(db_form)
    db.commit()
    db.refresh(db_form)
    return db_form

@router.get("/", response_model=List[InterviewFormResponse])
def get_interview_forms(
    skip: int = 0,
    limit: int = 100,
    candidate_id: Optional[str] = None,
    position: Optional[str] = None,
    start_date: Optional[datetime.datetime] = None,
    end_date: Optional[datetime.datetime] = None,
    db: Session = Depends(get_db)
):
    """Отримати список форм інтерв'ю з фільтрацією"""
    query = db.query(InterviewForm)
    
    # Застосування фільтрів
    if candidate_id:
        query = query.filter(InterviewForm.candidate_id == candidate_id)
    if position:
        query = query.filter(InterviewForm.position.ilike(f"%{position}%"))
    if start_date:
        query = query.filter(InterviewForm.interview_date >= start_date)
    if end_date:
        query = query.filter(InterviewForm.interview_date <= end_date)
    
    return query.offset(skip).limit(limit).all()

@router.get("/{interview_id}", response_model=InterviewFormDetailResponse)
def get_interview_form(interview_id: int, db: Session = Depends(get_db)):
    """Отримати форму інтерв'ю за ідентифікатором з деталями"""
    form = db.query(InterviewForm).filter(InterviewForm.id == interview_id).first()
    if form is None:
        raise HTTPException(status_code=404, detail="Форму інтерв'ю не знайдено")
    return form

@router.put("/{interview_id}", response_model=InterviewFormResponse)
def update_interview_form(interview_id: int, form: InterviewFormUpdate, db: Session = Depends(get_db)):
    """Оновити форму інтерв'ю"""
    db_form = db.query(InterviewForm).filter(InterviewForm.id == interview_id).first()
    if db_form is None:
        raise HTTPException(status_code=404, detail="Форму інтерв'ю не знайдено")
    
    # Оновлення тільки наданих полів
    update_data = form.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_form, key, value)
    
    db_form.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(db_form)
    return db_form

@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interview_form(interview_id: int, db: Session = Depends(get_db)):
    """Видалити форму інтерв'ю"""
    db_form = db.query(InterviewForm).filter(InterviewForm.id == interview_id).first()
    if db_form is None:
        raise HTTPException(status_code=404, detail="Форму інтерв'ю не знайдено")
    
    db.delete(db_form)
    db.commit()
    return {"detail": "Форму інтерв'ю видалено успішно"}

# Ендпоінти для роботи з інтерв'юерами
@router.post("/interviewers/", response_model=InterviewerResponse, status_code=status.HTTP_201_CREATED)
def create_interviewer(interviewer: InterviewerCreate, db: Session = Depends(get_db)):
    """Створити нового інтерв'юера"""
    # Перевірка унікальності email
    existing = db.query(Interviewer).filter(Interviewer.email == interviewer.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Інтерв'юер з таким email вже існує")
    
    db_interviewer = Interviewer(**interviewer.dict())
    db.add(db_interviewer)
    db.commit()
    db.refresh(db_interviewer)
    return db_interviewer

@router.get("/interviewers/", response_model=List[InterviewerResponse])
def get_interviewers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Отримати список інтерв'юерів"""
    return db.query(Interviewer).offset(skip).limit(limit).all()

@router.post("/{interview_id}/interviewers/{interviewer_id}", response_model=InterviewFormResponse)
def add_interviewer_to_form(interview_id: int, interviewer_id: int, db: Session = Depends(get_db)):
    """Додати інтерв'юера до форми"""
    form = db.query(InterviewForm).filter(InterviewForm.id == interview_id).first()
    if form is None:
        raise HTTPException(status_code=404, detail="Форму інтерв'ю не знайдено")
    
    interviewer = db.query(Interviewer).filter(Interviewer.id == interviewer_id).first()
    if interviewer is None:
        raise HTTPException(status_code=404, detail="Інтерв'юера не знайдено")
    
    # Перевірка, що інтерв'юер ще не доданий до форми
    if interviewer in form.interviewers:
        raise HTTPException(status_code=400, detail="Інтерв'юер вже доданий до цієї форми")
    
    form.interviewers.append(interviewer)
    db.commit()
    db.refresh(form)
    return form

@router.delete("/{interview_id}/interviewers/{interviewer_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_interviewer_from_form(interview_id: int, interviewer_id: int, db: Session = Depends(get_db)):
    """Видалити інтерв'юера з форми"""
    form = db.query(InterviewForm).filter(InterviewForm.id == interview_id).first()
    if form is None:
        raise HTTPException(status_code=404, detail="Форму інтерв'ю не знайдено")
    
    interviewer = db.query(Interviewer).filter(Interviewer.id == interviewer_id).first()
    if interviewer is None:
        raise HTTPException(status_code=404, detail="Інтерв'юера не знайдено")
    
    if interviewer not in form.interviewers:
        raise HTTPException(status_code=404, detail="Інтерв'юер не є учасником цієї форми")
    
    form.interviewers.remove(interviewer)
    db.commit()
    return {"detail": "Інтерв'юера видалено з форми успішно"}

# Ендпоінти для роботи з оцінками
@router.post("/{interview_id}/scores", response_model=ScoreResponse, status_code=status.HTTP_201_CREATED)
def add_score(interview_id: int, score: ScoreCreate, db: Session = Depends(get_db)):
    """Додати оцінку до форми інтерв'ю"""
    # Перевірка існування форми
    form = db.query(InterviewForm).filter(InterviewForm.id == interview_id).first()
    if form is None:
        raise HTTPException(status_code=404, detail="Форму інтерв'ю не знайдено")
    
    # Перевірка інтерв'юера
    interviewer = db.query(Interviewer).filter(Interviewer.id == score.interviewer_id).first()
    if interviewer is None:
        raise HTTPException(status_code=404, detail="Інтерв'юера не знайдено")
    
    # Перевірка, що інтерв'юер є учасником цієї форми
    if interviewer not in form.interviewers:
        raise HTTPException(status_code=400, detail="Інтерв'юер не є учасником цієї форми")
    
    # Перевірка питання
    question = db.query(Question).filter(Question.id == score.question_id).first()
    if question is None:
        raise HTTPException(status_code=404, detail="Питання не знайдено")
    
    # Створення оцінки
    db_score = Score(
        question_id=score.question_id,
        value=score.value,
        comment=score.comment,
        interviewer_id=score.interviewer_id,
        interview_form_id=interview_id
    )
    
    db.add(db_score)
    db.commit()
    db.refresh(db_score)
    return db_score

@router.get("/{interview_id}/scores", response_model=List[ScoreResponse])
def get_scores(interview_id: int, interviewer_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Отримати оцінки форми інтерв'ю"""
    # Перевірка існування форми
    form = db.query(InterviewForm).filter(InterviewForm.id == interview_id).first()
    if form is None:
        raise HTTPException(status_code=404, detail="Форму інтерв'ю не знайдено")
    
    query = db.query(Score).filter(Score.interview_form_id == interview_id)
    
    # Фільтрація за інтерв'юером
    if interviewer_id:
        query = query.filter(Score.interviewer_id == interviewer_id)
    
    return query.all()

# Ендпоінти для роботи з оцінюванням
@router.post("/{interview_id}/evaluations", response_model=EvaluationResponse, status_code=status.HTTP_201_CREATED)
def add_evaluation(interview_id: int, evaluation: EvaluationCreate, db: Session = Depends(get_db)):
    """Додати загальну оцінку кандидата"""
    # Перевірка існування форми
    form = db.query(InterviewForm).filter(InterviewForm.id == interview_id).first()
    if form is None:
        raise HTTPException(status_code=404, detail="Форму інтерв'ю не знайдено")
    
    # Створення оцінки
    db_evaluation = Evaluation(
        total_score=evaluation.total_score,
        passed=evaluation.passed,
        minimal_rate=evaluation.minimal_rate,
        interview_form_id=interview_id
    )
    
    db.add(db_evaluation)
    db.commit()
    db.refresh(db_evaluation)
    return db_evaluation

# Ендпоінти для роботи з відгуками
@router.post("/{interview_id}/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def add_feedback(interview_id: int, feedback: FeedbackCreate, db: Session = Depends(get_db)):
    """Додати відгук про кандидата"""
    # Перевірка існування форми
    form = db.query(InterviewForm).filter(InterviewForm.id == interview_id).first()
    if form is None:
        raise HTTPException(status_code=404, detail="Форму інтерв'ю не знайдено")
    
    # Перевірка, що відгук ще не існує
    existing = db.query(Feedback).filter(Feedback.interview_form_id == interview_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Відгук для цієї форми вже існує")
    
    # Створення відгуку
    db_feedback = Feedback(
        text=feedback.text,
        interview_form_id=interview_id
    )
    
    # Додавання заготовлених фраз
    for phrase_id in feedback.predefined_phrase_ids:
        phrase = db.query(PredefinedPhrase).filter(PredefinedPhrase.id == phrase_id).first()
        if phrase:
            db_feedback.phrases.append(phrase)
    
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback

# Ендпоінти для роботи з заготовленими фразами
@router.post("/phrases", response_model=PredefinedPhraseResponse, status_code=status.HTTP_201_CREATED)
def create_phrase(phrase: PredefinedPhraseCreate, db: Session = Depends(get_db)):
    """Створити нову заготовлену фразу"""
    db_phrase = PredefinedPhrase(**phrase.dict())
    db.add(db_phrase)
    db.commit()
    db.refresh(db_phrase)
    return db_phrase

@router.get("/phrases", response_model=List[PredefinedPhraseResponse])
def get_phrases(category: Optional[str] = None, db: Session = Depends(get_db)):
    """Отримати список заготовлених фраз"""
    query = db.query(PredefinedPhrase)
    
    # Фільтрація за категорією
    if category:
        query = query.filter(PredefinedPhrase.category == category)
    
    return query.all()
