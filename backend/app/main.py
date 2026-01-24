from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from app.models import GraphBuildRequest, GraphBuildResponse, GraphInsights, GraphVisualizationData
from app.nlp_engine import extract_entities
from app.relationship_logic import infer_relationships
from app.graph_db import graph_manager
from app.utils import extract_text_from_pdf
import uuid

app = FastAPI(
    title="Knowledge Graph Builder API",
    description="Convert unstructured documents into explainable knowledge graphs",
    version="1.0.0"
)

# CORS configuration - Updated for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:5174",  # Vite alternative port
        "http://localhost:3000",  # Alternative dev port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    db_status = "connected" if graph_manager.verify_connectivity() else "disconnected"
    return {
        "message": "Knowledge Graph Builder API",
        "status": "running",
        "database": db_status
    }

@app.get("/health")
async def health_check():
    db_status = "healthy" if graph_manager.verify_connectivity() else "unhealthy"
    return {
        "status": "healthy",
        "database": db_status
    }

@app.post("/build", response_model=GraphBuildResponse)
async def build_graph(request: GraphBuildRequest):
    """Processes text to build a knowledge graph."""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    session_id = request.session_id or f"sess-{uuid.uuid4().hex[:8]}"
    document_id = f"doc-{uuid.uuid4().hex[:8]}"
    
    try:
        # 1. NLP Processing
        entities, metadata = extract_entities(request.text, document_id=document_id)
        relationships = infer_relationships(request.text, metadata=metadata, document_id=document_id)
        
        # 2. Event Extraction
        from app.event_extraction import extract_events
        events = extract_events(request.text, entities, metadata, document_id=document_id)
        
        # 3. Persistence
        graph_manager.save_graph_data(session_id, entities, relationships, events)
        
        return GraphBuildResponse(
            session_id=session_id,
            entities=entities,
            relationships=relationships,
            events=events,
            message="Graph successfully built and persisted."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph building failed: {str(e)}")

@app.post("/upload", response_model=GraphBuildResponse)
async def upload_pdf(file: UploadFile = File(...), session_id: str = None):
    """Processes a PDF file to build a knowledge graph."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        contents = await file.read()
        text = extract_text_from_pdf(contents)
        
        if not text:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
            
        # Create request and process
        request = GraphBuildRequest(text=text, session_id=session_id)
        return await build_graph(request)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF processing failed: {str(e)}")

@app.delete("/clear")
async def clear_graph(session_id: str = Query(..., description="The session ID to clear")):
    """Clears graph data for a specific session."""
    try:
        graph_manager.clear_session(session_id)
        return {"message": f"Session {session_id} cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clear failed: {str(e)}")

@app.get("/insights", response_model=GraphInsights)
async def get_insights(session_id: str = Query(..., description="The session ID to analyze")):
    """Returns analytics for a specific session."""
    try:
        insights = graph_manager.get_insights(session_id)
        return GraphInsights(**insights)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insights failed: {str(e)}")

@app.get("/graph-data", response_model=GraphVisualizationData)
async def get_graph_data(session_id: str = Query(..., description="The session ID to visualize")):
    """Returns graph data formatted for vis-network visualization.
    
    This endpoint provides a secure way to get graph data without exposing
    Neo4j credentials to the frontend. Returns nodes and edges in vis-network format.
    """
    try:
        graph_data = graph_manager.get_graph_visualization_data(session_id)
        return GraphVisualizationData(**graph_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph data retrieval failed: {str(e)}")
