from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base  # 👈 IMPORTA OS MODELS!
import os

# Postgres
PG_DSN = f"postgresql://postgres:postgres@postgres:5432/tiktok_clone_python_development"
POSTGRES_URL = os.getenv("DATABASE_URL", PG_DSN)
engine_pg = create_engine(POSTGRES_URL)
SessionLocalPg = sessionmaker(autocommit=False, autoflush=False, bind=engine_pg)

# SQLite
SQLITE_URL = "sqlite:///./app.db"
engine_sqlite = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
SessionLocalSqlite = sessionmaker(bind=engine_sqlite)

def create_tables():
    print("🔄 CRIANDO POSTGRES...")
    Base.metadata.create_all(bind=engine_pg)  # 👈 Base.metadata!
    print("✅ POSTGRES OK!")
    
    print("🔄 CRIANDO SQLITE...")
    Base.metadata.create_all(bind=engine_sqlite)
    print("✅ SQLITE OK!")
    print("🎉 TUDO PRONTO!")