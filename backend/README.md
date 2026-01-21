# Knowledge Graph Builder - Backend

## Setup Instructions

### 1. Create Virtual Environment
```bash
python -m venv venv
```

### 2. Activate Virtual Environment
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Download SpaCy Model
```bash
python -m spacy download en_core_web_sm
```

### 5. Configure Environment Variables
```bash
# Copy example env file
copy .env.example .env

# Edit .env with your Neo4j credentials
```

### 6. Run Development Server
```bash
# Activate virtual environment first, then run:
uvicorn app.main:app --reload
```

### 7. Access API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── config.py        # Configuration management
│   └── models.py        # Pydantic models
├── requirements.txt     # Python dependencies
├── .env.example        # Environment template
└── README.md           # This file
```

## API Endpoints

### Health Check
- GET `/` - API information
- GET `/health` - Health status

## Tech Stack
- FastAPI 0.109.0
- Uvicorn (ASGI server)
- Pydantic (Data validation)
- SpaCy (NLP)
- Neo4j (Graph database)
