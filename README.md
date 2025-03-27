# FastAPI Contacts Management API

## 🚀 Overview
This project is a **FastAPI-based REST API** that allows users to manage their contacts. It includes authentication, email verification, JWT authorization, rate limiting, and avatar uploading via Cloudinary.

## 📌 Features
- **User Authentication & Authorization** (JWT-based)
- **User Registration with Email Verification**
- **CRUD Operations for Contacts**
- **User Rate Limiting** (SlowAPI)
- **CORS Support**
- **Cloudinary Integration for Avatar Uploads**
- **Docker & PostgreSQL Support**

## 🛠 Tech Stack
- **Python 3.11**
- **FastAPI**
- **SQLAlchemy** (PostgreSQL)
- **JWT (PyJWT & OAuth2)**
- **Passlib (Password Hashing)**
- **Cloudinary (Image Uploads)**
- **Docker & Docker Compose**
- **SlowAPI (Rate Limiting)**

## 🔧 Installation & Setup

### 1️⃣ **Clone the Repository**
```bash
git clone https://github.com/yourusername/fastapi-contacts.git
cd fastapi-contacts
```

### 2️⃣ **Create a Virtual Environment & Install Dependencies**
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

### 3️⃣ **Set Up Environment Variables**
Create a `.env` file and add:
```env
SECRET_KEY=your_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=postgresql://postgres:mysecretpassword@localhost:5432/fastapi_db
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_app_password
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### 4️⃣ **Run with Docker Compose**
```bash
docker-compose up --build
```

### 5️⃣ **Run PostgreSQL Locally (without Docker Compose)**
If using Docker manually, run:
```bash
docker run --name fastapi_db -p 5432:5432 -e POSTGRES_PASSWORD=mysecretpassword -d postgres
```
Or start an existing container:
```bash
docker start fastapi_db
```

### 6️⃣ **Run FastAPI Server**
```bash
uvicorn main:app --reload
```
The API will be available at: `http://127.0.0.1:8000`

### 7️⃣ **Useful Docker Commands**
#### Check running containers:
```bash
docker ps
```
#### Stop all containers:
```bash
docker-compose down
```
#### Restart the application:
```bash
docker-compose restart
```
#### View logs:
```bash
docker-compose logs -f
```
#### Remove all containers and volumes:
```bash
docker-compose down -v
```

## 📜 API Documentation
**Swagger UI:**
```
http://127.0.0.1:8000/docs
```
**ReDoc:**
```
http://127.0.0.1:8000/redoc
```

## 🔑 Authentication
1️⃣ **Register a new user:**
```http
POST /register/
```
2️⃣ **Verify email:**
```http
GET /verify/{token}
```
3️⃣ **Login to get JWT token:**
```http
POST /token
```
4️⃣ **Authorize in Swagger UI:**
- Click **Authorize** button.
- Enter: `Bearer <your_access_token>`.

## 📞 Contact Management
- **Create Contact:** `POST /contacts/`
- **Get Contacts:** `GET /contacts/`
- **Get Contact by ID:** `GET /contacts/{contact_id}`
- **Update Contact:** `PUT /contacts/{contact_id}`
- **Delete Contact:** `DELETE /contacts/{contact_id}`

## 🖼️ Upload Avatar
- **Upload Avatar:** `PUT /users/avatar/`
- File should be uploaded in **multipart/form-data** format.

## 🏗️ Project Structure
```
📁 fastapi-contacts/
│-- 📄 main.py          # Main FastAPI Application
│-- 📄 database.py      # Database Configuration
│-- 📄 models.py        # SQLAlchemy Models
│-- 📄 schemas.py       # Pydantic Schemas
│-- 📄 requirements.txt # Dependencies
│-- 📄 .env             # Environment Variables
│-- 📄 Dockerfile       # Docker Setup
│-- 📄 docker-compose.yml # Docker Compose Setup
```
