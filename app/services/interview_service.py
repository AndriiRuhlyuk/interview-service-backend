from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.db.models import (
    InterviewForm, ApplicationTemplate, Interviewer, 
    Score, Evaluation, Feedback, PredefinedPhrase, Question
)
from fastapi import HTTPException, status

class InterviewService:
    """
    Сервіс для роботи з формами співбесід
    """
    
    @staticmethod
    def get_interviews(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        candidate_id: Optional[str] = None,
        position: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[InterviewForm]:
        """
        Отримати список форм співбесід з можливістю фільтрації
        """
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
    
    @staticmethod
    def get_interview_by_id(db: Session, interview_id: int) -> InterviewForm:
        """
        Отримати форму співбесіди за ідентифікатором
        """
        interview = db.query(InterviewForm).filter(InterviewForm.id == interview_id).first()
        if interview is None:
            raise HTTPException(status_code=404, detail="Форму співбесіди не знайдено")
        return interview
    
    @staticmethod
    def create_interview(db: Session, interview_data: Dict[str, Any]) -> InterviewForm:
        """
        Створити нову форму співбесіди
        """
        # Перевірка існування шаблону
        template_id = interview_data.get('template_id')
        template = db.query(ApplicationTemplate).filter(ApplicationTemplate.id == template_id).first()
        if template is None:
            raise HTTPException(status_code=404, detail="Шаблон не знайдено")
        
        # Отримання даних інтерв'юерів
        interviewer_ids = interview_data.pop('interviewer_ids', [])
        
        # Створення форми співбесіди
        db_interview = InterviewForm(**interview_data)
        
        # Додавання інтерв'юерів
        for interviewer_id in interviewer_ids:
            interviewer = db.query(Interviewer).filter(Interviewer.id == interviewer_id).first()
            if interviewer is None:
                raise HTTPException(status_code=404, detail=f"Інтерв'юера з ID {interviewer_id} не знайдено")
            db_interview.interviewers.append(interviewer)
        
        db.add(db_interview)
        db.commit()
        db.refresh(db_interview)
        return db_interview
    
    @staticmethod
    def update_interview(db: Session, interview_id: int, interview_data: Dict[str, Any]) -> InterviewForm:
        """
        Оновити існуючу форму співбесіди
        """
        db_interview = InterviewService.get_interview_by_id(db, interview_id)
        
        # Оновлення тільки наданих полів
        for key, value in interview_data.items():
            setattr(db_interview, key, value)
        
        db.commit()
        db.refresh(db_interview)
        return db_interview
    
    @staticmethod
    def delete_interview(db: Session, interview_id: int) -> bool:
        """
        Видалити форму співбесіди
        """
        db_interview = InterviewService.get_interview_by_id(db, interview_id)
        db.delete(db_interview)
        db.commit()
        return True
    
    @staticmethod
    def add_score(db: Session, interview_id: int, score_data: Dict[str, Any]) -> Score:
        """
        Додати оцінку до форми співбесіди
        """
        # Перевірка існування форми
        interview = InterviewService.get_interview_by_id(db, interview_id)
        
        # Перевірка інтерв'юера
        interviewer_id = score_data.get('interviewer_id')
        interviewer = db.query(Interviewer).filter(Interviewer.id == interviewer_id).first()
        if interviewer is None:
            raise HTTPException(status_code=404, detail="Інтерв'юера не знайдено")
        
        # Перевірка, що інтерв'юер є учасником цієї форми
        if interviewer not in interview.interviewers:
            raise HTTPException(status_code=400, detail="Інтерв'юер не є учасником цієї форми")
        
        # Перевірка питання
        question_id = score_data.get('question_id')
        question = db.query(Question).filter(Question.id == question_id).first()
        if question is None:
            raise HTTPException(status_code=404, detail="Питання не знайдено")
        
        # Створення оцінки
        db_score = Score(
            question_id=question_id,
            value=score_data.get('value'),
            comment=score_data.get('comment'),
            interviewer_id=interviewer_id,
            interview_form_id=interview_id
        )
        
        db.add(db_score)
        db.commit()
        db.refresh(db_score)
        return db_score
    
    @staticmethod
    def get_scores(db: Session, interview_id: int, interviewer_id: Optional[int] = None) -> List[Score]:
        """
        Отримати оцінки форми співбесіди
        """
        # Перевірка існування форми
        InterviewService.get_interview_by_id(db, interview_id)
        
        query = db.query(Score).filter(Score.interview_form_id == interview_id)
        
        # Фільтрація за інтерв'юером
        if interviewer_id:
            query = query.filter(Score.interviewer_id == interviewer_id)
        
        return query.all()
    
    @staticmethod
    def add_evaluation(db: Session, interview_id: int, evaluation_data: Dict[str, Any]) -> Evaluation:
        """
        Додати загальну оцінку кандидата
        """
        # Перевірка існування форми
        interview = InterviewService.get_interview_by_id(db, interview_id)
        
        # Створення оцінки
        db_evaluation = Evaluation(
            total_score=evaluation_data.get('total_score'),
            passed=evaluation_data.get('passed'),
            minimal_rate=evaluation_data.get('minimal_rate'),
            interview_form_id=interview_id
        )
        
        db.add(db_evaluation)
        db.commit()
        db.refresh(db_evaluation)
        return db_evaluation
    
    @staticmethod
    def add_feedback(db: Session, interview_id: int, feedback_data: Dict[str, Any]) -> Feedback:
        """
        Додати відгук про кандидата
        """
        # Перевірка існування форми
        interview = InterviewService.get_interview_by_id(db, interview_id)
        
        # Перевірка, що відгук ще не існує
        existing = db.query(Feedback).filter(Feedback.interview_form_id == interview_id).first()
        if existing:
            # Якщо відгук вже існує, оновлюємо його
            existing.text = feedback_data.get('text')
            
            # Очищаємо і додаємо нові фрази
            existing.phrases = []
            predefined_phrase_ids = feedback_data.get('predefined_phrase_ids', [])
            for phrase_id in predefined_phrase_ids:
                phrase = db.query(PredefinedPhrase).filter(PredefinedPhrase.id == phrase_id).first()
                if phrase:
                    existing.phrases.append(phrase)
            
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # Створення відгуку
            db_feedback = Feedback(
                text=feedback_data.get('text'),
                interview_form_id=interview_id
            )
            
            # Додавання заготовлених фраз
            predefined_phrase_ids = feedback_data.get('predefined_phrase_ids', [])
            for phrase_id in predefined_phrase_ids:
                phrase = db.query(PredefinedPhrase).filter(PredefinedPhrase.id == phrase_id).first()
                if phrase:
                    db_feedback.phrases.append(phrase)
            
            db.add(db_feedback)
            db.commit()
            db.refresh(db_feedback)
            return db_feedback
    
    @staticmethod
    def create_interviewer(db: Session, interviewer_data: Dict[str, Any]) -> Interviewer:
        """
        Створити нового інтерв'юера
        """
        # Перевірка унікальності email
        existing = db.query(Interviewer).filter(Interviewer.email == interviewer_data.get('email')).first()
        if existing:
            raise HTTPException(status_code=400, detail="Інтерв'юер з таким email вже існує")
        
        db_interviewer = Interviewer(**interviewer_data)
        db.add(db_interviewer)
        db.commit()
        db.refresh(db_interviewer)
        return db_interviewer
    
    @staticmethod
    def get_interviewers(db: Session, skip: int = 0, limit: int = 100) -> List[Interviewer]:
        """
        Отримати список інтерв'юерів
        """
        return db.query(Interviewer).offset(skip).limit(limit).all()
    
    @staticmethod
    def add_interviewer_to_form(db: Session, interview_id: int, interviewer_id: int) -> InterviewForm:
        """
        Додати інтерв'юера до форми
        """
        interview = InterviewService.get_interview_by_id(db, interview_id)
        interviewer = db.query(Interviewer).filter(Interviewer.id == interviewer_id).first()
        
        if interviewer is None:
            raise HTTPException(status_code=404, detail="Інтерв'юера не знайдено")
        
        # Перевірка, що інтерв'юер ще не доданий до форми
        if interviewer in interview.interviewers:
            raise HTTPException(status_code=400, detail="Інтерв'юер вже доданий до цієї форми")
        
        interview.interviewers.append(interviewer)
        db.commit()
        db.refresh(interview)
        return interview
    
    @staticmethod
    def remove_interviewer_from_form(db: Session, interview_id: int, interviewer_id: int) -> bool:
        """
        Видалити інтерв'юера з форми
        """
        interview = InterviewService.get_interview_by_id(db, interview_id)
        interviewer = db.query(Interviewer).filter(Interviewer.id == interviewer_id).first()
        
        if interviewer is None:
            raise HTTPException(status_code=404, detail="Інтерв'юера не знайдено")
        
        if interviewer not in interview.interviewers:
            raise HTTPException(status_code=404, detail="Інтерв'юер не є учасником цієї форми")
        
        interview.interviewers.remove(interviewer)
        db.commit()
        return True
    
    @staticmethod
    def create_predefined_phrase(db: Session, phrase_data: Dict[str, Any]) -> PredefinedPhrase:
        """
        Створити нову заготовлену фразу
        """
        db_phrase = PredefinedPhrase(**phrase_data)
        db.add(db_phrase)
        db.commit()
        db.refresh(db_phrase)
        return db_phrase
    
    @staticmethod
    def get_predefined_phrases(db: Session, category: Optional[str] = None) -> List[PredefinedPhrase]:
        """
        Отримати список заготовлених фраз
        """
        query = db.query(PredefinedPhrase)
        
        # Фільтрація за категорією
        if category:
            query = query.filter(PredefinedPhrase.category == category)
        
        return query.all()
