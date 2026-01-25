# Knowledge Graph Builder

A sophisticated knowledge graph construction system that extracts structured entities and relationships from unstructured text using advanced NLP techniques and semantic validation.

## Overview

Knowledge Graph Builder transforms natural language text into clean, semantically valid knowledge graphs. The system employs SpaCy for named entity recognition, applies strict semantic validation rules, and stores the resulting graph in Neo4j for visualization and querying.

## Architecture

The system consists of three main components:

### Backend (FastAPI)
- NLP processing engine with SpaCy
- Semantic validation layer
- Entity and relationship extraction
- Neo4j database integration
- RESTful API endpoints

### Frontend (React + Vite)
- Interactive text input interface
- Real-time graph visualization
- Session management
- PDF upload support

### Database (Neo4j)
- Graph data storage
- Cypher query interface
- Relationship traversal
- Data persistence

## 📊 System Flow Diagrams

### High-Level Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[React UI<br/>Vite + React 18]
        Input[Input Panel<br/>Text/PDF Upload]
        Viz[Graph Visualization<br/>vis-network]
        Insights[Insights Panel<br/>Statistics]
    end
    
    subgraph "Backend Layer"
        API[FastAPI Server<br/>REST API]
        NLP[NLP Engine<br/>SpaCy]
        REL[Relationship Logic<br/>Pattern Matching]
        EVENT[Event Extraction<br/>Temporal Detection]
        VALID[Semantic Validator<br/>Type Checking]
    end
    
    subgraph "Database Layer"
        NEO[(Neo4j Graph DB<br/>Nodes & Edges)]
    end
    
    UI --> Input
    UI --> Viz
    UI --> Insights
    
    Input -->|HTTP POST| API
    API --> NLP
    NLP --> REL
    REL --> EVENT
    EVENT --> VALID
    VALID --> NEO
    
    NEO -->|Graph Data| API
    API -->|JSON Response| Viz
    API -->|Statistics| Insights
    
    style UI fill:#3b82f6,color:#fff
    style API fill:#10b981,color:#fff
    style NEO fill:#f59e0b,color:#fff
```

### Complete Data Flow Pipeline

```mermaid
flowchart TD
    Start([User Input]) --> InputType{Input Type?}
    
    InputType -->|Text| TextInput[Text Input]
    InputType -->|PDF| PDFInput[PDF Upload]
    
    PDFInput --> PDFExtract[PyPDF2 Extraction]
    PDFExtract --> TextInput
    
    TextInput --> SessionID[Generate/Use Session ID]
    SessionID --> DocID[Generate Document ID]
    
    DocID --> NLPStart[NLP Processing Start]
    
    subgraph "NLP Processing Pipeline"
        NLPStart --> SpaCy[SpaCy NER<br/>en_core_web_sm]
        SpaCy --> EntityExtract[Extract Entities<br/>PERSON, ORG, GPE, etc.]
        EntityExtract --> EntityNorm[Entity Normalization<br/>Remove Inc., LLC]
        EntityNorm --> EntityCat[Entity Categorization<br/>Structural vs Metadata]
        EntityCat --> MetaSep[Separate Metadata<br/>DATE, MONEY, PERCENT]
    end
    
    MetaSep --> RelStart[Relationship Inference Start]
    
    subgraph "Relationship Extraction"
        RelStart --> RoleDetect[Role-Based Detection<br/>CEO_OF, FOUNDED]
        RoleDetect --> LocDetect[Location Patterns<br/>HEADQUARTERED_IN]
        LocDetect --> ProdDetect[Product Patterns<br/>PRODUCES, RELEASED]
        ProdDetect --> SVOParse[SVO Dependency Parsing<br/>Subject-Verb-Object]
        SVOParse --> ConfScore[Confidence Scoring<br/>0.6 - 1.0]
    end
    
    ConfScore --> EventStart[Event Detection Start]
    
    subgraph "Event Extraction"
        EventStart --> AcqDetect[Acquisition Detection]
        AcqDetect --> LaunchDetect[Product Launch Detection]
        LaunchDetect --> LeaderDetect[Leadership Change Detection]
        LeaderDetect --> EventLink[Link Events to Entities]
    end
    
    EventLink --> Validate[Semantic Validation]
    
    subgraph "Validation Layer"
        Validate --> TypeCheck[Type Constraint Check<br/>PERSON → COMPANY valid?]
        TypeCheck --> ConfFilter[Confidence Filter<br/>threshold ≥ 0.6]
        ConfFilter --> DedupCheck[Deduplication Check]
    end
    
    DedupCheck --> Neo4jSave[Save to Neo4j]
    
    subgraph "Neo4j Storage"
        Neo4jSave --> CreateNodes[Create Entity Nodes]
        CreateNodes --> CreateEdges[Create Relationship Edges]
        CreateEdges --> AttachMeta[Attach Metadata Properties<br/>date, amount, source]
    end
    
    AttachMeta --> Response[Build API Response]
    Response --> FrontendUpdate[Update Frontend State]
    
    FrontendUpdate --> VizRequest[Request Graph Data]
    VizRequest --> Neo4jQuery[Query Neo4j for Visualization]
    Neo4jQuery --> FormatData[Format for vis-network<br/>nodes & edges]
    FormatData --> Render[Render Interactive Graph]
    
    Render --> End([User Views Graph])
    
    style Start fill:#3b82f6,color:#fff
    style End fill:#10b981,color:#fff
    style Neo4jSave fill:#f59e0b,color:#fff
    style Validate fill:#ef4444,color:#fff
```

### API Request-Response Flow

```mermaid
sequenceDiagram
    participant User
    participant React as React Frontend
    participant API as FastAPI Backend
    participant SpaCy as SpaCy NLP
    participant Neo4j as Neo4j Database
    
    User->>React: Enter text / Upload PDF
    React->>React: Set loading state
    
    React->>API: POST /build<br/>{text, session_id}
    
    API->>API: Generate session_id & document_id
    
    API->>SpaCy: extract_entities(text)
    SpaCy->>SpaCy: NER Processing
    SpaCy->>SpaCy: Entity Normalization
    SpaCy->>SpaCy: Metadata Separation
    SpaCy-->>API: entities[], metadata{}
    
    API->>API: infer_relationships(text, metadata)
    API->>API: Role-based detection
    API->>API: SVO parsing
    API->>API: Confidence scoring
    API-->>API: relationships[]
    
    API->>API: extract_events(text, entities)
    API->>API: Pattern matching
    API-->>API: events[]
    
    API->>API: Semantic validation
    API->>API: Type checking
    API->>API: Confidence filtering
    
    API->>Neo4j: save_graph_data(entities, relationships, events)
    Neo4j->>Neo4j: MERGE entities as nodes
    Neo4j->>Neo4j: MERGE relationships as edges
    Neo4j->>Neo4j: MERGE events with links
    Neo4j-->>API: Success
    
    API-->>React: {session_id, entities, relationships, events, message}
    
    React->>React: Update state
    React->>API: GET /graph-data?session_id=xxx
    
    API->>Neo4j: Query graph visualization data
    Neo4j->>Neo4j: MATCH (n)-[r]->(m)
    Neo4j-->>API: {nodes, edges}
    
    API-->>React: {nodes: [...], edges: [...]}
    
    React->>React: Render vis-network graph
    React->>User: Display interactive graph
    
    User->>React: Request insights
    React->>API: GET /insights?session_id=xxx
    
    API->>Neo4j: Query statistics
    Neo4j-->>API: {total_entities, total_relationships, entity_types}
    
    API-->>React: Insights data
    React->>User: Display statistics
```

### NLP Processing Detail

```mermaid
flowchart LR
    subgraph "Input"
        Text[Raw Text<br/>Apple acquired Beats for $3B in 2014]
    end
    
    subgraph "SpaCy NER"
        NER[Named Entity Recognition]
        Text --> NER
        NER --> E1[Apple - ORG]
        NER --> E2[Beats - ORG]
        NER --> E3[$3B - MONEY]
        NER --> E4[2014 - DATE]
    end
    
    subgraph "Entity Processing"
        E1 --> Norm1[Normalize: Apple]
        E2 --> Norm2[Normalize: Beats]
        E3 --> Meta1[Metadata: amount]
        E4 --> Meta2[Metadata: date]
        
        Norm1 --> Cat1[Structural Entity]
        Norm2 --> Cat2[Structural Entity]
    end
    
    subgraph "Relationship Inference"
        Cat1 --> Pattern[Pattern Match: acquired]
        Cat2 --> Pattern
        Pattern --> Rel[Apple -ACQUIRED-> Beats]
        Meta1 --> Rel
        Meta2 --> Rel
    end
    
    subgraph "Event Detection"
        Pattern --> Event[Acquisition Event]
        Event --> EventProps[name: Apple acquires Beats<br/>type: Acquisition<br/>participants: Apple, Beats<br/>amount: $3B<br/>date: 2014]
    end
    
    subgraph "Output"
        Cat1 --> Out1[Entity: Apple ORG]
        Cat2 --> Out2[Entity: Beats ORG]
        Rel --> Out3[Relationship: ACQUIRED<br/>metadata: amount=$3B, date=2014]
        EventProps --> Out4[Event Node with INVOLVES edges]
    end
    
    style Text fill:#3b82f6,color:#fff
    style Out1 fill:#10b981,color:#fff
    style Out2 fill:#10b981,color:#fff
    style Out3 fill:#f59e0b,color:#fff
    style Out4 fill:#8b5cf6,color:#fff
```

### Neo4j Graph Structure

```mermaid
graph TB
    subgraph "Entity Nodes"
        P1((Person<br/>Tim Cook))
        C1((Company<br/>Apple))
        C2((Company<br/>Beats))
        PR1((Product<br/>iPhone))
        L1((Location<br/>Cupertino))
    end
    
    subgraph "Event Nodes"
        E1{Acquisition<br/>Apple acquires Beats<br/>$3B, 2014}
        E2{Product Launch<br/>iPhone Release<br/>2007}
    end
    
    P1 -->|CEO_OF<br/>confidence: 0.95| C1
    C1 -->|ACQUIRED<br/>amount: $3B<br/>date: 2014| C2
    C1 -->|RELEASED<br/>date: 2007| PR1
    C1 -->|HEADQUARTERED_IN| L1
    
    E1 -.->|INVOLVES| C1
    E1 -.->|INVOLVES| C2
    E2 -.->|INVOLVES| C1
    E2 -.->|INVOLVES| PR1
    
    style P1 fill:#3b82f6,color:#fff
    style C1 fill:#10b981,color:#fff
    style C2 fill:#10b981,color:#fff
    style PR1 fill:#8b5cf6,color:#fff
    style L1 fill:#f59e0b,color:#fff
    style E1 fill:#fbbf24,color:#000
    style E2 fill:#ec4899,color:#fff
```

## System Workflow

### 1. Text Input
Users submit unstructured text through the web interface or PDF upload.

### 2. NLP Processing
```
Input Text → SpaCy NER → Entity Extraction → Entity Type Correction → Semantic Filtering
```

**Entity Detection:**
- Extract named entities using SpaCy's en_core_web_sm model
- Apply entity type correction for known companies/products
- Force-detect common products (Echo, Alexa, etc.)
- Filter to allowed types: PERSON, COMPANY, PRODUCT, ORGANIZATION, LOCATION
- Remove metadata entities (DATE, MONEY, PERCENT) - stored as properties

**Supported Entity Types:**
- PERSON: Individuals, executives
- COMPANY: Corporations, businesses (normalized from ORG)
- PRODUCT: Commercial products, services
- ORGANIZATION: Non-profit organizations
- LOCATION: Cities, countries, regions (normalized from GPE)

### 3. Relationship Extraction
```
Entities + Text → Pattern Matching → Relationship Detection → Semantic Validation → Valid Relationships
```

**Extraction Strategies:**
- Role-based detection (CEO_OF, FOUNDED, EMPLOYED_BY)
- Location patterns (HEADQUARTERED_IN, LOCATED_IN)
- Product patterns (PRODUCES, RELEASED, DEVELOPS)
- Competition detection (COMPETES_WITH)
- List-based patterns ("such as X, Y, Z", "companies like X, Y, Z")
- SVO (Subject-Verb-Object) dependency parsing

**Supported Relationships:**
- FOUNDED: Person → Company
- CEO_OF / FORMER_CEO_OF: Person → Company (temporal distinction)
- EMPLOYED_BY: Person → Company/Organization
- PRODUCES / RELEASED / DEVELOPS: Company → Product
- OPERATES: Company → Organization
- LOCATED_IN / HEADQUARTERED_IN: Company → Location
- COMPETES_WITH: Company ← → Company
- COLLABORATES_WITH: Company ← → Company
- ACQUIRED: Company → Company

### 4. Semantic Validation
```
Extracted Relationships → Type Checking → Confidence Filtering → Validated Relationships
```

**Validation Rules:**
- Each relationship enforces entity type constraints
- Minimum confidence threshold (0.6)
- Invalid semantic triples are rejected
- Example: PERSON → PRODUCES → PRODUCT is invalid (requires COMPANY → PRODUCT)

### 5. Graph Storage
```
Validated Data → Neo4j Cypher Queries → Graph Database → Persistence
```

**Storage Strategy:**
- Entities stored as nodes with properties
- Relationships stored as edges with metadata
- Dates and monetary values attached as relationship properties
- Unique constraints on (entity name, entity type) pairs

### 6. Visualization
```
Neo4j Graph → Frontend API → React Force Graph → Interactive Visualization
```

**Visualization Features:**
- Color-coded nodes by entity type
- Directed relationship edges
- Interactive node exploration
- Session-based graph management

## Technical Stack

### Backend
- **Framework:** FastAPI
- **NLP:** SpaCy (en_core_web_sm)
- **Database:** Neo4j (Aura cloud or local)
- **Validation:** Custom semantic validator
- **Language:** Python 3.11+

### Frontend
- **Framework:** React 18
- **Build Tool:** Vite
- **Visualization:** react-force-graph
- **HTTP Client:** Fetch API
- **Language:** JavaScript (ES6+)

### Database
- **Graph DB:** Neo4j 5.x
- **Query Language:** Cypher
- **Driver:** neo4j-python-driver

## Installation

### Prerequisites
- Python 3.11 or higher
- Node.js 18 or higher
- Neo4j database (local or Aura cloud)

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Create `.env` file in backend directory:
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

Run backend server:
```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at `http://localhost:5173`

## API Documentation

### Build Graph
**POST** `/build`

Request:
```json
{
  "text": "Amazon was founded by Jeff Bezos in 1994.",
  "session_id": "optional-session-id"
}
```

Response:
```json
{
  "session_id": "sess-abc123",
  "entities": [
    {"text": "Amazon", "type": "ORG"},
    {"text": "Jeff Bezos", "type": "PERSON"}
  ],
  "relationships": [
    {
      "source": "Jeff Bezos",
      "target": "Amazon",
      "type": "FOUNDED",
      "confidence": 0.95,
      "metadata": {"date": "1994"}
    }
  ],
  "events": [],
  "message": "Graph built: 2 entities, 1 relationships validated."
}
```

### Other Endpoints
- **POST** `/upload` - Upload PDF document
- **GET** `/graph-data?session_id=xxx` - Retrieve graph data
- **DELETE** `/clear?session_id=xxx` - Clear session graph
- **GET** `/insights?session_id=xxx` - Get graph insights

## Extraction Rules

### Entity Type Correction
The system automatically corrects SpaCy misclassifications:
- Alibaba (GPE) → Company (ORG)
- Kindle (GPE) → Product (PRODUCT)
- Echo (not detected) → Product (PRODUCT) via force detection

### List Pattern Detection
Handles multiple entities in lists:
- "produces devices such as Kindle, Echo, Fire TV" → 3 PRODUCES relationships
- "competes with Microsoft, Google, Alibaba" → 3 COMPETES_WITH relationships

### Temporal Role Detection
Distinguishes current vs. former roles:
- "Tim Cook is CEO of Apple" → CEO_OF
- "Steve Jobs was CEO of Apple" → FORMER_CEO_OF

## Development

### Project Structure
```
knowledge-graph-builder/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── nlp_engine.py        # Entity extraction
│   │   ├── relationship_logic.py # Relationship detection
│   │   ├── extraction_rules.py   # Validation rules
│   │   ├── semantic_validator.py # Filtering logic
│   │   ├── graph_manager.py     # Neo4j interface
│   │   └── models.py            # Data models
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main component
│   │   ├── components/          # UI components
│   │   └── services/api.js      # API client
│   ├── package.json
│   └── README.md
└── README.md
```

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Configuration

### Environment Variables

**Backend (.env):**
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
MIN_CONFIDENCE_THRESHOLD=0.6
```

### Customization

**Add Custom Entity Types:**
Edit `backend/app/extraction_rules.py` and add to `AllowedEntityType` enum.

**Add Custom Relationships:**
1. Add to `AllowedRelationshipType` enum
2. Define semantic rules in `SEMANTIC_RULES` dict
3. Add detection patterns in `relationship_logic.py`

**Adjust Confidence Threshold:**
Modify `MIN_CONFIDENCE_THRESHOLD` in `relationship_logic.py`

## Troubleshooting

### Common Issues

**Neo4j Connection Failed:**
- Verify Neo4j is running
- Check credentials in `.env`
- Ensure correct URI format

**SpaCy Model Not Found:**
```bash
python -m spacy download en_core_web_sm
```

**CORS Errors:**
- Ensure backend allows frontend origin in `main.py`
- Check that frontend is running on expected port

**Missing Relationships:**
- Check backend console for validation logs
- Verify entity types are correct
- Ensure confidence threshold is not too high

## Performance Considerations

- **Text Length:** SpaCy max_length set to 2,000,000 characters
- **Deduplication:** Entity and relationship deduplication automatically applied
- **Database:** Neo4j constraints ensure data integrity
- **Caching:** Session-based caching for improved performance

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome. Please ensure:
- Code follows existing patterns
- Tests pass before submitting
- Documentation is updated
- Semantic validation rules are maintained

## Support

For issues or questions, please open a GitHub issue.
