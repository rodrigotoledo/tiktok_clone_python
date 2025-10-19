from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import shutil
import os
from datetime import datetime, timedelta  # 👈 ADICIONAR timedelta AQUI
from pydantic import BaseModel

# Nossos imports - APENAS OS BÁSICOS
from database import create_tables, get_db
from models import User, Post, Comment  # 👈 APENAS ESTES TRÊS
from config import APP_ENV, ACCESS_TOKEN_EXPIRE_MINUTES
from auth import (
    authenticate_user, create_access_token, get_password_hash,
    verify_token, security
)

class UserCreate(BaseModel):
    email_address: str
    password: str

class UserLogin(BaseModel):
    email_address: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

app = FastAPI(
    title="TikTok Clone API",
    description="Clone do TikTok com FastAPI + PostgreSQL",
    docs_url="/docs" if APP_ENV == "development" else None
)

# CORS para o frontend Vite
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
      "http://localhost:3000", "http://127.0.0.1:3000",
      "http://localhost:5173", "http://127.0.0.1:5173"
      ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração de uploads
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Servir arquivos estáticos (IMPORTANTE: depois de definir app)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.on_event("startup")
async def startup():
    print(f"🚀 Iniciando TikTok Clone em modo: {APP_ENV}")
    create_tables()
    print("✅ Todas as tabelas criadas/verificadas!")

# ===== ROTAS DE AUTENTICAÇÃO =====

@app.post("/auth/signup", response_model=dict)
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

    return {
        "message": "Usuário criado com sucesso",
        "user_id": user.id,
        "email": user.email_address
    }

@app.post("/auth/signin", response_model=Token)
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
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  # 👈 AGORA FUNCIONA
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
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
        "tabelas": ["users", "posts", "comments"]  # 👈 ATUALIZADO
    }

@app.get("/health")
async def health(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {"status": "OK", "ambiente": APP_ENV, "database": db_status}

# ===== ROTAS PROTEGIDAS =====

@app.post("/upload/video")
async def upload_video(
    title: str = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)  # 👈 AGORA É PROTEGIDO!
):
    # Verifica se é um vídeo
    if not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="Arquivo deve ser um vídeo")

    # Salva o arquivo localmente
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Salva no banco com o user_id REAL do usuário autenticado
    post = Post(
        title=title,
        body=description,
        attachment=f"/uploads/{filename}",
        video_filename=file.filename,
        user_id=current_user.id  # 👈 AGORA USA O USER REAL!
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    return {
        "message": "Vídeo uploaded com sucesso!",
        "post_id": post.id,
        "file_url": f"/uploads/{filename}",
        "video_url": f"http://localhost:8000/uploads/{filename}"
    }

@app.post("/posts/{post_id}/comments")
async def create_comment(
    post_id: int,
    body: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)  # 👈 AGORA É PROTEGIDO!
):
    """Adiciona comentário a um post"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")

    comment = Comment(
        post_id=post_id,
        user_id=current_user.id,  # 👈 AGORA USA O USER REAL!
        body=body
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return {"message": "Comentário adicionado", "comment_id": comment.id}

# ===== ROTAS PÚBLICAS =====

@app.get("/posts")
async def list_posts(db: Session = Depends(get_db)):
    """Lista todos os posts (videos) - Público"""
    posts = db.query(Post).order_by(Post.created_at.desc()).all()

    return {
        "posts": [
            {
                "id": p.id,
                "title": p.title,
                "body": p.body,
                "attachment": p.attachment,
                "video_url": f"http://localhost:8000{p.attachment}" if p.attachment else None,
                "user_id": p.user_id,
                "created_at": p.created_at.isoformat() if p.created_at else None
            } for p in posts
        ]
    }

@app.get("/posts/{post_id}")
async def get_post(post_id: int, db: Session = Depends(get_db)):
    """Busca um post específico - Público"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")

    return {
        "id": post.id,
        "title": post.title,
        "body": post.body,
        "attachment": post.attachment,
        "video_url": f"http://localhost:8000{post.attachment}" if post.attachment else None,
        "user_id": post.user_id,
        "created_at": post.created_at.isoformat() if post.created_at else None  # 👈 CORRIGIDO: post.created_at
    }

@app.get("/posts/{post_id}/comments")
async def get_comments(post_id: int, db: Session = Depends(get_db)):
    """Lista comentários de um post - Público"""
    comments = db.query(Comment).filter(Comment.post_id == post_id).order_by(Comment.created_at.desc()).all()

    return {
        "comments": [
            {
                "id": c.id,
                "body": c.body,
                "user_id": c.user_id,
                "created_at": c.created_at.isoformat() if c.created_at else None
            } for c in comments
        ]
    }

# ===== ROTA PARA TESTE RÁPIDO =====
@app.post("/test/upload")
async def test_upload():
    return {
        "message": "Upload endpoint está funcionando!",
        "instructions": "Use /upload/video com form-data: title, description, file"
    }
