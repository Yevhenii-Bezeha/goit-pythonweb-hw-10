import os
import smtplib
from datetime import datetime, timedelta, date
from email.message import EmailMessage
from typing import List, Optional
import cloudinary
import cloudinary.uploader
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import EmailStr
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session, relationship
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from starlette.requests import Request
from dotenv import load_dotenv
from database import SessionLocal, engine, Base
from models import Contact, User, ContactResponse, ContactCreate

load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)


Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_user(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(db: Session, email: str, password: str):
    user = get_user(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        user = get_user(db, email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def send_verification_email(email: str, token: str):
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT"))
    smtp_email = os.getenv("SMTP_EMAIL")
    smtp_password = os.getenv("SMTP_PASSWORD")

    msg = EmailMessage()
    msg["Subject"] = "Verify your email"
    msg["From"] = smtp_email
    msg["To"] = email
    msg.set_content(f"Click the link to verify your email: http://127.0.0.1:8000/verify/{token}")

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_email, smtp_password)
        server.send_message(msg)


@app.post("/contacts/", response_model=ContactResponse)
def create_contact(contact: ContactCreate, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    db_contact = Contact(**contact.dict(), owner_id=current_user.id)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


@app.get("/contacts/", response_model=List[ContactResponse])
def read_contacts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Contact).filter(Contact.owner_id == current_user.id).all()


@app.get("/contacts/{contact_id}", response_model=ContactResponse)
def read_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.owner_id == current_user.id).first()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@app.put("/contacts/{contact_id}", response_model=ContactResponse)
def update_contact(contact_id: int, contact_data: ContactCreate, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.owner_id == current_user.id).first()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    for key, value in contact_data.dict().items():
        setattr(contact, key, value)
    db.commit()
    db.refresh(contact)
    return contact


@app.delete("/contacts/{contact_id}", response_model=ContactResponse)
def delete_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.owner_id == current_user.id).first()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(contact)
    db.commit()
    return contact


limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

@app.get("/me/")
@limiter.limit("5/minute")
async def read_users_me(request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        user = get_user(db, email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/register/")
def register_user(email: EmailStr, password: str, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="User already exists")
    hashed_password = pwd_context.hash(password)
    user = User(email=email, hashed_password=hashed_password, is_verified=False)
    db.add(user)
    db.commit()
    db.refresh(user)
    verification_token = create_access_token({"sub": email})
    send_verification_email(email, verification_token)
    return {"message": "User registered successfully. Please check your email to verify your account."}


@app.get("/verify/{token}")
def verify_email(token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=400, detail="Invalid token")
        user.is_verified = True
        db.commit()
        return {"message": "Email verified successfully"}
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")


@app.put("/users/avatar/")
def update_avatar(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        upload_result = cloudinary.uploader.upload(file.file)
        current_user.avatar_url = upload_result["secure_url"]
        db.commit()
        db.refresh(current_user)
        return {"message": "Avatar updated successfully", "avatar_url": current_user.avatar_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading avatar: {str(e)}")


@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}