import os
import smtplib
from datetime import datetime, timedelta, date
from email.message import EmailMessage
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from consts import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, pwd_context, oauth2_scheme
from database import SessionLocal
from models import User

load_dotenv()



# OAuth2 scheme


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
