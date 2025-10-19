from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import shutil
import os
from datetime import datetime

# Nossos imports
from database import create_tables, get_db
from models import User, Post, Comment, Following, Session as UserSession, Account
from config import APP_ENV

app = FastAPI(
    title="TikTok Clone API",
    description="Clone do TikTok com FastAPI + PostgreSQL",
    docs_url="/docs" if APP_ENV == "development" else None
)

# CORS para o frontend Vite
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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

# ===== ROTAS BÁSICAS =====
@app.get("/")
async def root():
    return {
        "message": "🚀 TikTok Clone API está rodando!",
        "ambiente": APP_ENV,
        "tabelas": ["users", "posts", "comments", "accounts", "followings", "sessions"]
    }

@app.get("/health")
async def health(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {"status": "OK", "ambiente": APP_ENV, "database": db_status}

# ===== UPLOAD DE VÍDEOS =====
@app.post("/upload/video")
async def upload_video(
    title: str = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
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

    # Salva no banco (user_id temporário - depois usa JWT)
    post = Post(
        title=title,
        body=description,
        attachment=f"/uploads/{filename}",
        video_filename=file.filename,
        user_id=1  # TODO: Pegar do usuário autenticado
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    return {
        "message": "Vídeo uploaded com sucesso!",
        "post_id": post.id,
        "file_url": f"/uploads/{filename}",
        "video_url": f"http://localhost:8000/uploads/{filename}"  # URL completa
    }

# ===== ROTAS DE POSTS =====
@app.get("/posts")
async def list_posts(db: Session = Depends(get_db)):
    """Lista todos os posts (videos)"""
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
    """Busca um post específico"""
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
        "created_at": post.created_at.isoformat() if post.created_at else None
    }

# ===== ROTAS DE USUÁRIOS =====
@app.post("/users")
async def create_user(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """Cria um novo usuário"""
    # Verifica se já existe
    existing_user = db.query(User).filter(User.email_address == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    # TODO: Hash da senha com bcrypt
    user = User(
        email_address=email,
        password_digest=password  # Em produção: hash this!
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "Usuário criado", "user_id": user.id}

@app.get("/users")
async def list_users(db: Session = Depends(get_db)):
    """Lista todos os usuários"""
    users = db.query(User).all()
    return {
        "users": [
            {
                "id": u.id,
                "email": u.email_address,
                "created_at": u.created_at.isoformat() if u.created_at else None
            } for u in users
        ]
    }

# ===== ROTAS DE COMENTÁRIOS =====
@app.post("/posts/{post_id}/comments")
async def create_comment(
    post_id: int,
    body: str = Form(...),
    db: Session = Depends(get_db)
):
    """Adiciona comentário a um post"""
    # Verifica se o post existe
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")

    comment = Comment(
        post_id=post_id,
        user_id=1,  # TODO: Pegar do usuário autenticado
        body=body
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return {"message": "Comentário adicionado", "comment_id": comment.id}

@app.get("/posts/{post_id}/comments")
async def get_comments(post_id: int, db: Session = Depends(get_db)):
    """Lista comentários de um post"""
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
    """Rota para testar se o upload está funcionando"""
    return {
        "message": "Upload endpoint está funcionando!",
        "instructions": "Use /upload/video com form-data: title, description, file"
    }
