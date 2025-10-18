from fastapi import FastAPI
from database import create_tables
from models import User, Post, Comment

app = FastAPI(title="Meu App Python = Rails!")

@app.on_event("startup")
async def startup():
    create_tables()

@app.get("/")
async def root():
    return {
        "message": "🚀 Schema Rails → Python OK!",
        "tabelas": ["users", "posts", "comments", "accounts", "followings", "sessions"]
    }

@app.get("/health")
async def health():
    return {"status": "OK", "bancos": "Postgres + SQLite"}