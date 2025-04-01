import os
from datetime import date, timedelta
from typing import List
import cloudinary
import cloudinary.uploader
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import EmailStr
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session, relationship
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from starlette.requests import Request
from dotenv import load_dotenv

from consts import SECRET_KEY, ALGORITHM, pwd_context, oauth2_scheme
from database import engine, Base
from models import Contact, User, ContactResponse, ContactCreate
from utils import get_db, get_current_user, create_access_token, send_verification_email, authenticate_user, get_user

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
def update_avatar(file: UploadFile = File(...), db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
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


@app.get("/contacts/upcoming_birthdays/", response_model=List[ContactResponse])
def get_upcoming_birthdays_for_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today = date.today()
    next_week = today + timedelta(days=7)

    if today.month == 2 and today.day == 29:
        feb_28 = date(today.year, 2, 28)
        next_week = feb_28 + timedelta(days=7)

    contacts = (
        db.query(Contact)
        .filter(
            Contact.user_id == current_user.id,
            Contact.birthday.between(today, next_week)
        )
        .all()
    )
    return contacts