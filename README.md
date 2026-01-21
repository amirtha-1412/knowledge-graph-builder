# Knowledge Graph Builder

## Project Overview
Convert unstructured enterprise documents into structured, explainable knowledge graphs for analysis and insight discovery.

## Architecture
```
User Input (Text/PDF)
        ↓
   React Frontend (Port 5173)
        ↓
   FastAPI Backend (Port 8000)
        ↓
   SpaCy NLP Engine
        ↓
   Neo4j Graph Database
        ↓
   Interactive Visualization
```

## Tech Stack

### Frontend
- React 19.2.0
- Vite 7.2.4
- vis-network 10.0.2
- Axios 1.13.2

### Backend
- FastAPI 0.109.0
- Uvicorn 0.27.0
- SpaCy 3.7.2
- Neo4j 5.16.0
- PyPDF2 3.0.1

## Quick Start

### Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl
uvicorn app.main:app --reload
```

Backend runs at: http://localhost:8000

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:5173

## Project Structure
```
knowledge-graph-builder/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   └── models.py
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── package.json
└── README.md
```

