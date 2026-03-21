import time, io, base64, qrcode
from fastapi import FastAPI, Depends, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import engine, Base, get_db
from models import User
from auth_utils import hash_password, verify_password

Base.metadata.create_all(bind=engine)
app = FastAPI()

@app.on_event("startup")
def create_admin():
    db = next(get_db())
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        user = User(
            full_name="Администратор СКУД",
            position="Начальник охраны",
            username="admin",
            hashed_password=hash_password("admin123"),
            is_admin=True
        )
        db.add(user); db.commit()

@app.post("/api/register")
def register(
    full_name: str=Form(...), 
    position: str=Form(...), 
    username: str=Form(...), 
    password: str=Form(...), 
    admin_id: int=Form(None), 
    db: Session=Depends(get_db)
):
    if admin_id:
        admin = db.query(User).filter(User.id == admin_id, User.is_admin == True).first()
        if not admin:
            raise HTTPException(status_code=403, detail="Ошибка прав")
    
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Логин занят")
        
    user = User(
        full_name=full_name, 
        position=position, 
        username=username, 
        hashed_password=hash_password(password),
        is_admin=False
    )
    db.add(user); db.commit()
    return {"status": "ok"}

@app.post("/api/login")
def login(username: str=Form(...), password: str=Form(...), db: Session=Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401)
    return {"id": user.id, "full_name": user.full_name, "position": user.position, "is_admin": user.is_admin}

@app.get("/api/generate_qr/{user_id}")
def generate_qr(user_id: int, db: Session=Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    ts = int(time.time())
    qr_data = f"RTK_PASS|ID:{user.id}|NAME:{user.full_name}|POS:{user.position}|TS:{ts}"
    img = qrcode.make(qr_data)
    buf = io.BytesIO()
    img.save(buf)
    return {"qr": base64.b64encode(buf.getvalue()).decode(), "expires": 300}

@app.post("/api/verify_qr")
async def verify_qr(qr_data: str = Form(...)):
    try:
        parts = qr_data.split('|')
        if parts[0] != "RTK_PASS": return {"status": "error", "message": "Не формат Ростелеком"}
        data = {p.split(':', 1)[0]: p.split(':', 1)[1] for p in parts[1:]}
        if int(time.time()) - int(data['TS']) > 300:
            return {"status": "error", "message": "Пропуск истек"}
        return {"status": "success", "name": data['NAME'], "position": data['POS'], "id": data['ID']}
    except: return {"status": "error", "message": "Код не распознан"}

app.mount("/", StaticFiles(directory="static", html=True), name="static")