from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import questions, templates, interviews, integrations
from app.db.database import engine
from app.db.models import Base

# Створення таблиць в базі даних (в реальному проекті варто використовувати Alembic для міграцій)
Base.metadata.create_all(bind=engine)

# Створення додатку FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API для сервісу проведення технічних співбесід"
)

# Налаштування CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Включення роутерів API
app.include_router(questions.router)
app.include_router(templates.router)
app.include_router(interviews.router)
app.include_router(integrations.router)

@app.get("/")
async def root():
    """Основний ендпоінт"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "message": "Ласкаво просимо до сервісу проведення технічних співбесід"
    }

@app.get("/health")
async def health():
    """Ендпоінт для перевірки стану сервісу"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
