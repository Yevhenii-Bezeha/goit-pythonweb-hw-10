# 🧠 FastAPI + PostgreSQL App

This is a web application built with FastAPI and PostgreSQL, fully containerized using Docker Compose. It supports hot-reloading for development and follows a modular structure for scalability.

## 🚀 Tech Stack

- FastAPI – modern, high-performance web framework for APIs
- PostgreSQL – relational database
- Docker & Docker Compose – containerized development
- SQLAlchemy – ORM for database interactions
- Pydantic – data validation and serialization

## ⚙️ Setup Instructions

1. Clone the repository

git clone https://github.com/AnastasiaRiabova/goit-pythonweb-hw-10
cd goit-pythonweb-hw-10

2. Configure environment variables

Copy the example environment file:

cp .env.example .env

Then edit .env with your values:

SECRET_KEY=
DATABASE_URL=
CLOUDINARY_URL=
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
ALGORITHM=
ACCESS_TOKEN_EXPIRE_MINUTES=
SMTP_SERVER=
SMTP_PORT=
SMTP_EMAIL=
SMTP_PASSWORD=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=

3. Run the project

docker-compose up --build

The API will be available at: http://localhost:8000

## 📫 API Endpoints

FastAPI provides built-in interactive documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

If you'd like a written list of endpoints with request/response examples, I can auto-generate that for you — just say the word!

## 🧪 Testing

Tests are not yet included, but the structure supports easy integration using pytest.

## 📄 License

MIT License — free to use, modify, and distribute.
