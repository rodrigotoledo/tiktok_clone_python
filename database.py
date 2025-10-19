from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from config import DATABASE_URL, SQLITE_URL, APP_ENV  # 👈 IMPORTA DIRETO AS VARIÁVEIS
import sys

print("🔧 Configurando database...")
print(f"   DATABASE_URL: {DATABASE_URL}")

# Postgres
engine_pg = create_engine(DATABASE_URL)
SessionLocalPg = sessionmaker(autocommit=False, autoflush=False, bind=engine_pg)

# SQLite
engine_sqlite = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
SessionLocalSqlite = sessionmaker(bind=engine_sqlite)

def create_tables():
    print("🔄 Criando tabelas no Postgres...")
    Base.metadata.create_all(bind=engine_pg)
    print("✅ Postgres OK!")

    print("🔄 Criando tabelas no SQLite...")
    Base.metadata.create_all(bind=engine_sqlite)
    print("✅ SQLite OK!")

def get_db():
    if APP_ENV == "development":
        db = SessionLocalSqlite()
    else:
        db = SessionLocalPg()

    try:
        yield db
    finally:
        db.close()
