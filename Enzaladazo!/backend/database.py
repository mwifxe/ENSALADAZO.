from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Determinar el ambiente
ENV = os.getenv("ENV", "development")

if ENV == "production":
    # PostgreSQL para producción (Render)
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Render proporciona DATABASE_URL con postgres://, pero SQLAlchemy necesita postgresql://
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    # SQLite para desarrollo
    DATABASE_URL = "sqlite:///./ensaladazo.db"
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )

# Crear sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()

# Dependencia para obtener la sesión de DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()