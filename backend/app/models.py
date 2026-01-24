from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class EntityCategory(str, Enum):
    """Categorize entities as structural (for nodes) or metadata (for properties)"""
    STRUCTURAL = "structural"  # PERSON, ORG, GPE, PRODUCT, EVENT, FAC, WORK_OF_ART
    METADATA = "metadata"      # DATE, MONEY, PERCENT, CARDINAL, ORDINAL

class EntityMetadata(BaseModel):
    """Metadata properties for enriching entities and relationships"""
    date: Optional[str] = None
    amount: Optional[str] = None
    percentage: Optional[float] = None
    quantity: Optional[int] = None
    location: Optional[str] = None

class Entity(BaseModel):
    text: str
    type: str
    category: EntityCategory = EntityCategory.STRUCTURAL
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    context: Optional[str] = None
    source_sentence: Optional[str] = None
    document_id: Optional[str] = None
    properties: Optional[EntityMetadata] = None

class Relationship(BaseModel):
    source: str
    target: str
    type: str
    reason: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    verb: Optional[str] = None
    source_sentence: Optional[str] = None
    document_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None  # For date, amount, etc.

class EventType(str, Enum):
    """Types of events to extract"""
    ACQUISITION = "Acquisition"
    PRODUCT_LAUNCH = "ProductLaunch"
    LEADERSHIP_CHANGE = "LeadershipChange"
    CONFERENCE = "Conference"
    FUNDING_ROUND = "FundingRound"
    OTHER = "Other"

class Event(BaseModel):
    """Event node for temporal, transaction-based facts"""
    event_type: EventType
    name: str
    participants: List[str]  # Entity names involved
    date: Optional[str] = None
    location: Optional[str] = None
    amount: Optional[str] = None
    context: str
    document_id: Optional[str] = None
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)

class GraphBuildRequest(BaseModel):
    text: str
    session_id: Optional[str] = None

class GraphBuildResponse(BaseModel):
    session_id: str
    entities: List[Entity]
    relationships: List[Relationship]
    events: List[Event] = []
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
