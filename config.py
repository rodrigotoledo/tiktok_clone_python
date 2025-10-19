import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/tiktok_clone")
POSTGRES_DB = os.getenv("POSTGRES_DB", "tiktok_clone")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# SQLite
SQLITE_URL = os.getenv("SQLITE_URL", "sqlite:///./app.db")

# App
APP_ENV = os.getenv("APP_ENV", "development")
SECRET_KEY = os.getenv("SECRET_KEY", "chave_temporaria_mudar_depois")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Debug
if APP_ENV == "development":
    print("🔧 Configurações carregadas:")
    print(f"   DATABASE_URL: {DATABASE_URL}")
