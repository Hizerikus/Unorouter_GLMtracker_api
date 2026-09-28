from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator

from config import settings
from models import Base


engine = create_engine(f"sqlite:///{settings.database.path}", echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()