from fastapi import FastAPI, Depends, HTTPException, Request, File, Form, status, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
import shutil
import os
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Union

# Nossos imports
from database import get_db  # 👈 REMOVA create_tables daqui
from models import User, Post, Comment, Following, Account
from config import APP_ENV, ACCESS_TOKEN_EXPIRE_MINUTES
from auth import (
    authenticate_user, create_token, get_password_hash,
    verify_token, security
)

class UserCreate(BaseModel):
    email_address: str
    password: str

class UserLogin(BaseModel):
    email_address: str
    password: str

class Token(BaseModel):
    token: str
    token_type: str

app = FastAPI(
    title="TikTok Clone API",
    description="Clone do TikTok com FastAPI + PostgreSQL",
    docs_url="/docs" if APP_ENV == "development" else None
)

@app.middleware("http")
async def debug_middleware(request: Request, call_next):
    # Log das requisições
    print(f"📨 {request.method} {request.url}")
    print(f"📋 Headers: {dict(request.headers)}")

    response = await call_next(request)

    # Log das respostas
    print(f"📤 Response: {response.status_code}")
    return response

# CORS para o frontend Vite
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas as origens
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"]  # Adiciona esta linha
)

# Configuração de uploads
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Servir arquivos estáticos (IMPORTANTE: depois de definir app)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.on_event("startup")
async def startup():
    print(f"🚀 Iniciando TikTok Clone em modo: {APP_ENV}")
    print("📡 Conectando ao database...")
    # Apenas verifica a conexão, não cria tabelas
    try:
        db = next(get_db())
        db.execute("SELECT 1")
        print("✅ Conectado ao database com sucesso!")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")


# ===== ROTAS DE AUTENTICAÇÃO =====

@app.post("/registration", response_model=dict)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """Registra um novo usuário"""
    # Verifica se já existe
    existing_user = db.query(User).filter(User.email_address == user_data.email_address).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verifique o email informado"
        )

    # Cria usuário com senha hasheada
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email_address=user_data.email_address,
        password_digest=hashed_password
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  # 👈 AGORA FUNCIONA
    token = create_token(
        data={"sub": str(user.id)}, expires_delta=token_expires
    )

    return {
        "message": "Usuário criado com sucesso",
        "user_id": user.id,
        "email_address": user.email_address,
        "token": token,
        "token_type": "bearer"
    }

@app.post("/session", response_model=Token)
async def signin(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login do usuário"""
    user = authenticate_user(db, user_data.email_address, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Cria token JWT
    token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  # 👈 AGORA FUNCIONA
    token = create_token(
        data={"sub": str(user.id)}, expires_delta=token_expires
    )

    return {
        "token": token,
        "email_address": user.email_address,
        "token_type": "bearer"
    }

@app.get("/auth/me")
async def get_current_user(current_user: User = Depends(verify_token)):
    """Retorna informações do usuário atual"""
    return {
        "id": current_user.id,
        "email_address": current_user.email_address,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }

# ===== ROTAS BÁSICAS =====
@app.get("/")
async def root():
    return {
        "message": "🚀 TikTok Clone API está rodando!",
        "ambiente": APP_ENV,
        "tabelas": ["users", "posts", "comments", "followings", "accounts"]  # 👈 ATUALIZADO
    }


# ===== ROTAS PROTEGIDAS =====

class CommentCreate(BaseModel):
    body: str

class FrontendCommentRequest(BaseModel):
    method: str
    comment: CommentCreate

@app.post("/posts/{post_id}/comments")
async def create_comment(
    post_id: int,
    request_data: FrontendCommentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """Adiciona comentário a um post"""
    print(f"🎯 Criando comentário: {request_data.comment.body}")

    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")

    comment = Comment(
        post_id=post_id,
        user_id=current_user.id,
        body=request_data.comment.body
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return {
        "message": "Comentário adicionado",
        "comment_id": comment.id,
        "comment": {
            "id": comment.id,
            "body": comment.body,
            "user_id": comment.user_id,
            "created_at": comment.created_at.isoformat() if comment.created_at else None
        }
    }

@app.get("/posts")
async def list_posts(
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """Lista todos os posts (videos) - PROTEGIDO"""
    # Use joinedload para carregar o usuário junto
    from sqlalchemy.orm import joinedload

    posts = db.query(Post).options(joinedload(Post.user)).order_by(Post.created_at.desc()).all()

    return {
        "posts": [
            {
                "id": p.id,
                "title": p.title,
                "body": p.body,
                "user_id": p.user_id,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "user": {  # 👈 AGORA INCLUI OS DADOS DO USUÁRIO
                    "id": p.user.id,
                    "email_address": p.user.email_address,
                    "created_at": p.user.created_at.isoformat() if p.user.created_at else None
                }
            } for p in posts
        ]
    }

@app.get("/posts/{post_id}/comments")
async def get_comments(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)  # 👈 ADICIONAR AQUI
):
    """Lista comentários de um post - PROTEGIDO"""
    comments = db.query(Comment).filter(Comment.post_id == post_id).order_by(Comment.created_at.desc()).all()

    return {
        "comments": [
            {
                "id": c.id,
                "body": c.body,
                "user_id": c.user_id,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "user": {  # 👈 AGORA INCLUI OS DADOS DO USUÁRIO
                    "id": c.user.id,
                    "email_address": c.user.email_address,
                    "created_at": c.user.created_at.isoformat() if c.user.created_at else None
                }
            } for c in comments
        ]
    }
