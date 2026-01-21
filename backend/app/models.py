from pydantic import BaseModel
from typing import List, Optional

class Entity(BaseModel):
    text: str
    type: str

class Relationship(BaseModel):
    source: str
    target: str
    type: str
    reason: str

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
    entity_types: dict
