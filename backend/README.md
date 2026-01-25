# Knowledge Graph Builder - Backend

FastAPI-based backend service for extracting entities and relationships from unstructured text using SpaCy NLP and storing them in Neo4j graph database.

## Architecture

The backend implements a multi-stage NLP pipeline:

```
Text Input → Entity Extraction → Type Correction → Semantic Validation → Relationship Detection → Graph Storage
```

## Core Components

### 1. NLP Engine (`nlp_engine.py`)

Responsible for entity extraction and initial processing.

**Functions:**
- `extract_entities(text)` - Extract named entities using SpaCy
- `correct_entity_type()` - Fix entity type misclassifications
- `extract_metadata()` - Extract temporal and numeric metadata
- `normalize_entity_name()` - Standardize entity names

**Entity Processing Flow:**
1. Clean and normalize input text
2. Run SpaCy NER to detect entities
3. Apply entity type corrections (e.g., Alibaba GPE → ORG)
4. Force-detect common products (Echo, Alexa, etc.)
5. Filter to allowed entity types
6. Apply semantic validation
7. Deduplicate entities

**Supported Entity Types:**
- PERSON - Individuals
- COMPANY - Corporations (normalized from ORG)
- PRODUCT - Commercial products
- ORGANIZATION - Non-profit organizations
- LOCATION - Geographic locations (normalized from GPE)

### 2. Relationship Logic (`relationship_logic.py`)

Handles relationship extraction through multiple strategies.

**Extraction Strategies:**

**Strategy 1: Sentence-Level Co-occurrence**
- Detects entities in same sentence
- Applies role-based patterns (CEO_OF, FOUNDED, etc.)
- Uses location indicators (headquartered, based in)
- Detects product relationships (produces, released)
- LIST-based patterns ("such as X, Y, Z")

**Strategy 2: SVO Dependency Parsing**
- Extracts Subject-Verb-Object triples
- Maps verbs to relationship types
- Calculates confidence scores

**Pattern Examples:**
```python
# Role-based
"Jeff Bezos is CEO of Amazon" → (Jeff Bezos)-[CEO_OF]->(Amazon)

# List-based products
"Amazon produces Kindle, Echo, Fire TV" → 
  (Amazon)-[PRODUCES]->(Kindle)
  (Amazon)-[PRODUCES]->(Echo)
  (Amazon)-[PRODUCES]->(Fire TV)

# List-based competition
"Amazon competes with Microsoft, Google, Alibaba" →
  (Amazon)-[COMPETES_WITH]->(Microsoft)
  (Amazon)-[COMPETES_WITH]->(Google)
  (Amazon)-[COMPETES_WITH]->(Alibaba)

# Temporal detection
"Steve Jobs was CEO" → FORMER_CEO_OF
"Tim Cook is CEO" → CEO_OF
```

### 3. Semantic Validator (`semantic_validator.py`)

Enforces semantic correctness of extracted data.

**Validation Rules:**
- Entity types must be in allowed list
- Relationships must follow semantic constraints
- Confidence must meet minimum threshold

**Semantic Constraints:**
```
FOUNDED: PERSON → COMPANY
CEO_OF: PERSON → COMPANY
PRODUCES: COMPANY → PRODUCT
LOCATED_IN: COMPANY → LOCATION
COMPETES_WITH: COMPANY ← → COMPANY
```

**Invalid Examples (Rejected):**
- PERSON → PRODUCES → PRODUCT (should be COMPANY)
- LOCATION → LOCATED_IN → LOCATION
- PRODUCT → CEO_OF → COMPANY

### 4. Extraction Rules (`extraction_rules.py`)

Centralized configuration for validation rules.

**Contents:**
- `AllowedEntityType` enum - 5 entity types
- `AllowedRelationshipType` enum - 13 relationship types
- `SEMANTIC_RULES` dict - Allowed (source, rel, target) triples
- `validate_relationship_semantics()` - Core validation function

### 5. Graph Manager (`graph_manager.py`)

Handles all Neo4j database operations.

**Key Functions:**
- `create_entity()` - Create entity node
- `create_relationship()` - Create relationship edge
- `create_event()` - Create event node
- `clear_graph()` - Clear session graphs
- `get_graph_data()` - Retrieve graph for visualization

**Neo4j Schema:**
```cypher
// Entities
CREATE (e:Entity {
  name: "Amazon",
  type: "ORG",
  session_id: "sess-123"
})

// Relationships
CREATE (a)-[r:FOUNDED {
  confidence: 0.95,
  date: "1994",
  session_id: "sess-123"
}]->(b)

// Constraints
CREATE CONSTRAINT entity_unique_name IF NOT EXISTS
FOR (e:Entity) REQUIRE (e.name, e.type) IS UNIQUE
```

### 6. API Endpoints (`main.py`)

FastAPI application with RESTful endpoints.

**Endpoints:**

**POST** `/build`
- Accept text input
- Extract entities and relationships
- Store in Neo4j
- Return structured response

**POST** `/upload`
- Accept PDF file
- Extract text using PyPDF2
- Process through NLP pipeline
- Store results

**GET** `/graph-data?session_id={id}`
- Retrieve graph for visualization
- Return nodes and edges in force-graph format

**DELETE** `/clear?session_id={id}`
- Clear all graph data for session
- Return confirmation

**GET** `/insights?session_id={id}`
- Return graph statistics
- Entity counts by type
- Relationship counts

## Installation

### Prerequisites
- Python 3.11+
- Neo4j database (local or Aura cloud)

### Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Download SpaCy model:
```bash
python -m spacy download en_core_web_sm
```

4. Create `.env` file:
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
MIN_CONFIDENCE_THRESHOLD=0.6
```

### Run Server

```bash
uvicorn app.main:app --reload --port 8000
```

API will be available at `http://localhost:8000`

## Configuration

### Environment Variables

```env
NEO4J_URI=bolt://localhost:7687        # Neo4j connection URI
NEO4J_USER=neo4j                        # Neo4j username
NEO4J_PASSWORD=password                 # Neo4j password
MIN_CONFIDENCE_THRESHOLD=0.6            # Minimum relationship confidence
```

### Customization

**Add New Entity Type:**
1. Add to `AllowedEntityType` enum in `extraction_rules.py`
2. Update normalization in `nlp_engine.py`
3. Add semantic rules if needed

**Add New Relationship:**
1. Add to `AllowedRelationshipType` enum
2. Define semantic rules in `SEMANTIC_RULES`
3. Add detection pattern in `relationship_logic.py`

**Adjust Thresholds:**
- Modify `MIN_CONFIDENCE_THRESHOLD` for relationship acceptance
- Adjust distance penalty in `calculate_confidence()`

## API Reference

### Build Graph Endpoint

```http
POST /build
Content-Type: application/json

{
  "text": "Amazon was founded by Jeff Bezos in Seattle.",
  "session_id": "optional-session-id"
}
```

Response:
```json
{
  "session_id": "sess-abc123",
  "entities": [
    {
      "text": "Jeff Bezos",
      "type": "PERSON",
      "category": "STRUCTURAL"
    },
    {
      "text": "Amazon",
      "type": "ORG",
      "category": "STRUCTURAL"
    },
    {
      "text": "Seattle",
      "type": "GPE",
      "category": "STRUCTURAL"
    }
  ],
  "relationships": [
    {
      "source": "Jeff Bezos",
      "target": "Amazon",
      "type": "FOUNDED",
      "confidence": 0.95,
      "reason": "Role-based detection",
      "metadata": null
    },
    {
      "source": "Amazon",
      "target": "Seattle",
      "type": "LOCATED_IN",
      "confidence": 0.85,
      "reason": "Location detection",
      "metadata": null
    }
  ],
  "events": [],
  "message": "Graph built: 3 entities, 2 relationships validated."
}
```

## Testing

Run tests with pytest:
```bash
pytest tests/
```

Test specific module:
```bash
python -m app.nlp_engine  # Test entity extraction
python -m app.relationship_logic  # Test relationship extraction
```

## Logging

The backend provides detailed console logging:

```
[Entity Extraction] Total entities before filtering: 15
[Entity Extraction] Total entities after filtering: 12
  - Jeff Bezos (PERSON)
  - Amazon (ORG)
  - Kindle (PRODUCT)

[Force Detection] Added missing product: Echo

[Relationship Extraction] Total relationships before validation: 18
  - Amazon -[PRODUCES]-> Kindle (confidence: 0.85)
  - Amazon -[COMPETES_WITH]-> Microsoft (confidence: 0.85)

[Relationship Extraction] Total relationships after validation: 15
```

## Error Handling

```python
# Neo4j connection errors
try:
    manager.create_entity(entity)
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Graph building failed: {str(e)}")

# SpaCy processing errors
try:
    entities, metadata = extract_entities(text)
except Exception as e:
    logger.error(f"Entity extraction failed: {e}")
    raise
```

## Performance

- **Throughput:** ~100 entities/second
- **Latency:** <500ms for typical paragraph
- **Max Text Length:** 2,000,000 characters (configurable)
- **Concurrent Requests:** Unlimited (async FastAPI)

## Dependencies

```
fastapi==0.109.0
uvicorn==0.27.0
spacy==3.7.2
neo4j==5.16.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-multipart==0.0.6
PyPDF2==3.0.1
```

## Troubleshooting

**SpaCy Model Not Found:**
```bash
python -m spacy download en_core_web_sm
```

**Neo4j Connection Failed:**
- Verify Neo4j is running
- Check credentials in `.env`
- Test connection: `neo4j://localhost:7687`

**Import Errors:**
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

**CORS Issues:**
- Update allowed origins in `main.py`
- Add frontend URL to CORS middleware

## Development

### Project Structure
```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── nlp_engine.py        # Entity extraction
│   ├── relationship_logic.py # Relationship detection
│   ├── extraction_rules.py   # Validation rules
│   ├── semantic_validator.py # Filtering logic
│   ├── graph_manager.py     # Neo4j interface
│   ├── models.py            # Pydantic models
│   └── config.py            # Configuration
├── tests/
│   └── test_extraction.py
├── requirements.txt
├── .env
└── README.md
```

### Code Style
- Follow PEP 8 conventions
- Use type hints
- Document complex functions
- Write tests for new features

## License

MIT License
