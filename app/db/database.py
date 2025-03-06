from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Створення URL-з'єднання з базою даних
SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"

# Створення екземпляра движка бази даних
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Створення класу сесії
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовий клас для всіх моделей
Base = declarative_base()

# Отримання з'єднання з базою даних
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
