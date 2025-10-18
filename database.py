from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
import os

# Postgres
PG_DSN = f"postgresql://postgres:postgres@postgres:5432/tiktok_clone_python_development"
POSTGRES_URL = os.getenv("DATABASE_URL", PG_DSN)
engine_pg = create_engine(POSTGRES_URL)
SessionLocalPg = sessionmaker(autocommit=False, autoflush=False, bind=engine_pg)

# SQLite (arquivo mapeado!)
SQLITE_URL = "sqlite:///./app.db"
engine_sqlite = create_engine(SQLITE_URL)
SessionLocalSqlite = sessionmaker(bind=engine_sqlite)

metadata = MetaData()

def create_tables():
    metadata.create_all(engine_pg)
    metadata.create_all(engine_sqlite)
    print("✅ Tabelas criadas em Postgres E SQLite!")