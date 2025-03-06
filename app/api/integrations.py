from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.db.database import get_db
from app.db.models import InterviewForm, Evaluation, Feedback
from app.config import settings
import httpx
import json
from pydantic import BaseModel

router = APIRouter(prefix="/api/integrations/peopleforce", tags=["integrations"])

# Клас для роботи з PeopleForce API
class PeopleForceClient:
    def __init__(self):
        self.base_url = settings.PEOPLEFORCE_API_URL
        self.api_key = settings.PEOPLEFORCE_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def get_candidates(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Отримати список кандидатів з PeopleForce"""
        url = f"{self.base_url}/api/v1/candidates"
        params = filters or {}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Помилка отримання кандидатів з PeopleForce: {response.text}"
                )
            
            return response.json()
    
    async def get_candidate(self, candidate_id: str) -> Dict[str, Any]:
        """Отримати інформацію про кандидата за ID"""
        url = f"{self.base_url}/api/v1/candidates/{candidate_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Помилка отримання кандидата з PeopleForce: {response.text}"
                )
            
            return response.json()
    
    async def update_candidate_notes(self, candidate_id: str, notes: str) -> Dict[str, Any]:
        """Оновити нотатки кандидата"""
        url = f"{self.base_url}/api/v1/candidates/{candidate_id}"
        payload = {"notes": notes}
        
        async with httpx.AsyncClient() as client:
            response = await client.patch(url, headers=self.headers, json=payload)
            
            if response.status_code not in (200, 201, 204):
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Помилка оновлення нотаток кандидата в PeopleForce: {response.text}"
                )
            
            return response.json()
    
    async def add_candidate_attachment(self, candidate_id: str, file_name: str, file_content: bytes, file_type: str) -> Dict[str, Any]:
        """Додати вкладення до кандидата"""
        url = f"{self.base_url}/api/v1/candidates/{candidate_id}/attachments"
        
        # Оновити заголовки для multipart/form-data
        headers = self.headers.copy()
        headers.pop("Content-Type", None)
        
        files = {
            "file": (file_name, file_content, file_type)
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, files=files)
            
            if response.status_code not in (200, 201, 204):
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Помилка додавання вкладення до кандидата в PeopleForce: {response.text}"
                )
            
            return response.json()


# Pydantic моделі для запитів і відповідей
class CandidateResponse(BaseModel):
    id: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    status: Optional[str] = None


# Ендпоінти для роботи з PeopleForce API
@router.get("/candidates", response_model=List[CandidateResponse])
async def get_candidates(
    search: Optional[str] = None,
    position: Optional[str] = None,
    status: Optional[str] = None
):
    """Отримати список кандидатів з PeopleForce"""
    client = PeopleForceClient()
    
    filters = {}
    if search:
        filters["q"] = search
    if position:
        filters["position"] = position
    if status:
        filters["status"] = status
    
    candidates = await client.get_candidates(filters)
    
    # Трансформація даних у потрібний формат
    result = []
    for candidate in candidates:
        result.append(
            CandidateResponse(
                id=candidate["id"],
                full_name=candidate.get("full_name", ""),
                email=candidate.get("email", ""),
                phone=candidate.get("phone", ""),
                position=candidate.get("position", ""),
                status=candidate.get("status", "")
            )
        )
    
    return result

@router.get("/candidates/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(candidate_id: str):
    """Отримати інформацію про кандидата за ID"""
    client = PeopleForceClient()
    
    candidate = await client.get_candidate(candidate_id)
    
    return CandidateResponse(
        id=candidate["id"],
        full_name=candidate.get("full_name", ""),
        email=candidate.get("email", ""),
        phone=candidate.get("phone", ""),
        position=candidate.get("position", ""),
        status=candidate.get("status", "")
    )

@router.post("/{interview_id}/sync", status_code=status.HTTP_200_OK)
async def sync_interview_to_peopleforce(interview_id: int, db: Session = Depends(get_db)):
    """Синхронізувати результати інтерв'ю з PeopleForce"""
    # Отримати дані форми інтерв'ю
    form = db.query(InterviewForm).filter(InterviewForm.id == interview_id).first()
    if form is None:
        raise HTTPException(status_code=404, detail="Форму інтерв'ю не знайдено")
    
    # Отримати оцінки та відгуки
    evaluations = db.query(Evaluation).filter(Evaluation.interview_form_id == interview_id).all()
    feedback = db.query(Feedback).filter(Feedback.interview_form_id == interview_id).first()
    
    # Підготувати дані для відправки
    notes = f"## Результати технічної співбесіди\n\n"
    notes += f"**Позиція:** {form.position}\n"
    notes += f"**Дата інтерв'ю:** {form.interview_date.strftime('%Y-%m-%d %H:%M')}\n\n"
    
    # Додати інформацію про інтерв'юерів
    notes += "**Інтерв'юери:**\n"
    for interviewer in form.interviewers:
        notes += f"- {interviewer.name} ({interviewer.position})\n"
    
    notes += "\n**Оцінки:**\n"
    
    # Обчислення загальної оцінки
    if evaluations:
        for eval in evaluations:
            passed_text = "Пройшов" if eval.passed else "Не пройшов"
            notes += f"- Загальна оцінка: {eval.total_score} з {eval.minimal_rate} необхідних\n"
            notes += f"- Результат: {passed_text}\n\n"
    
    # Додати відгук
    if feedback:
        notes += "**Відгук:**\n"
        notes += feedback.text
        
        if feedback.phrases:
            notes += "\n\n**Рекомендації:**\n"
            for phrase in feedback.phrases:
                notes += f"- {phrase.text}\n"
    
    # Відправити дані у PeopleForce
    client = PeopleForceClient()
    
    try:
        # Оновити нотатки кандидата
        await client.update_candidate_notes(form.candidate_id, notes)
        
        # Створити PDF з результатами і відправити як вкладення
        # В реальному проекті тут варто використати якусь бібліотеку для створення PDF
        # і відправити його через add_candidate_attachment
        
        return {"status": "success", "message": "Дані успішно синхронізовано з PeopleForce"}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Помилка при синхронізації даних з PeopleForce: {str(e)}"
        )
