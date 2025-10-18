from fastapi import FastAPI
from database import engine_pg, create_tables

app = FastAPI(title="Meu Projeto Python")

# Cria tabelas na inicialização
@app.on_event("startup")
async def startup():
    create_tables()

@app.get("/")
async def root():
    return {"message": "🚀 FastAPI rodando!", "bancos": "Postgres + SQLite"}

@app.get("/health")
async def health():
    return {"status": "OK"}