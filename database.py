from sqlalchemy import create_engine, text, inspect  # 👈 ADICIONE inspect
from sqlalchemy.orm import sessionmaker
from models import Base
from config import DATABASE_URL, SQLITE_URL, APP_ENV
import sys

print("🔧 Configurando database...")
print(f"   DATABASE_URL: {DATABASE_URL}")

# Postgres
engine_pg = create_engine(DATABASE_URL)
SessionLocalPg = sessionmaker(autocommit=False, autoflush=False, bind=engine_pg)

# SQLite
engine_sqlite = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
SessionLocalSqlite = sessionmaker(bind=engine_sqlite)

def drop_tables():
    """Dropa todas as tabelas na ordem correta (considerando FKs)"""
    print("🗑️  Dropando tabelas no Postgres...")

    # Para Postgres: desabilita constraints temporariamente
    with engine_pg.connect() as conn:
        # Desabilita constraints
        conn.execute(text("SET session_replication_role = 'replica';"))

        # Drop todas as tabelas
        Base.metadata.drop_all(bind=engine_pg)

        # Re-habilita constraints
        conn.execute(text("SET session_replication_role = 'origin';"))
        conn.commit()

    print("✅ Postgres OK!")

    print("🗑️  Dropando tabelas no SQLite...")
    # Para SQLite: drop normal (SQLite lida melhor com FKs)
    Base.metadata.drop_all(bind=engine_sqlite)
    print("✅ SQLite OK!")

def create_tables():
    """Cria todas as tabelas"""
    print("🔄 Criando tabelas no Postgres...")
    Base.metadata.create_all(bind=engine_pg)
    print("✅ Postgres OK!")

    print("🔄 Criando tabelas no SQLite...")
    Base.metadata.create_all(bind=engine_sqlite)
    print("✅ SQLite OK!")

def reset_database():
    """Dropa e recria todas as tabelas"""
    print("🚀 Iniciando reset do database...")
    drop_tables()
    create_tables()
    print("🎉 Database resetado com sucesso!")

def check_tables_exist():
    """Verifica se as tabelas existem (apenas para logging)"""
    try:
        inspector = inspect(engine_pg)
        tables = inspector.get_table_names()
        print(f"📊 Tabelas existentes: {len(tables)}")
        return len(tables) > 0
    except Exception as e:
        print(f"⚠️  Não foi possível verificar tabelas: {e}")
        return False

def get_db():
    """Retorna sessão do banco - SEM criar tabelas automaticamente"""
    db = SessionLocalPg()
    try:
        yield db
    finally:
        db.close()
