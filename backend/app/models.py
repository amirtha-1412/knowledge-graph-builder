from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Entity(BaseModel):
    text: str
    type: str
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    context: Optional[str] = None

class Relationship(BaseModel):
    source: str
    target: str
    type: str
    reason: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    verb: Optional[str] = None

class GraphBuildRequest(BaseModel):
    text: str
    session_id: Optional[str] = None

class GraphBuildResponse(BaseModel):
    session_id: str
    entities: List[Entity]
    relationships: List[Relationship]
    message: str

class GraphInsights(BaseModel):
    total_entities: int
    total_relationships: int
    most_connected_entity: Optional[str] = None
    entity_types: Dict[str, int]
    avg_confidence: Optional[float] = None

class GraphVisualizationData(BaseModel):
    """Data structure for graph visualization"""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
