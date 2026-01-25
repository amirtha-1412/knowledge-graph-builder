# Knowledge Graph Builder - Frontend

React-based web interface for interacting with the Knowledge Graph Builder system. Provides text input, PDF upload, and interactive graph visualization.

## Architecture

The frontend is built with React and Vite, providing a fast development experience and optimized production builds.

```
User Interface → API Client → Backend → Graph Visualization
```

## Core Components

### 1. App Component (`App.jsx`)

Main application container managing state and coordinating sub-components.

**State Management:**
- `graphData` - Current graph nodes and edges
- `sessionId` - Current session identifier
- `loading` - Loading state for async operations
- `error` - Error messages from API calls

**Flow:**
```
User Input → handleBuildGraph() → API Call → Update State → Re-render Graph
```

### 2. Input Panel (`InputPanel.jsx`)

Text input and PDF upload interface.

**Features:**
- Multi-line text input with clear button
- PDF file upload and processing
- Submit button with loading state
- Character count display
- Error messaging

**Props:**
```javascript
{
  onTextSubmit: (text) => void,     // Handle text submission
  onFileUpload: (file) => void,     // Handle PDF upload
  loading: boolean,                  // Show loading state
  onClear: () => void               // Clear input
}
```

### 3. Graph Viewer (`GraphViewer.jsx`)

Interactive graph visualization using react-force-graph.

**Features:**
- Force-directed layout
- Color-coded nodes by entity type
- Directional edges with labels
- Zoom and pan controls
- Node click interactions

**Node Colors:**
```javascript
{
  PERSON: '#4A90E2',        // Blue
  ORG: '#50C878',           // Green (Companies)
  PRODUCT: '#9B59B6',       // Purple
  GPE: '#F39C12',           // Orange (Locations)
  ORGANIZATION: '#1ABC9C'   // Teal
}
```

**Graph Data Format:**
```javascript
{
  nodes: [
    {
      id: "Amazon",
      name: "Amazon",
      type: "ORG",
      color: "#50C878"
    }
  ],
  links: [
    {
      source: "Jeff Bezos",
      target: "Amazon",
      type: "FOUNDED",
      label: "FOUNDED"
    }
  ]
}
```

### 4. InsightsPanel (`InsightsPanel.jsx`)

Displays statistics about the knowledge graph.

**Metrics Shown:**
- Total entities by type
- Total relationships by type
- Session information
- Graph density metrics

**Component Structure:**
```javascript
<InsightsPanel
  sessionId={sessionId}
  entityCount={12}
  relationshipCount={15}
  insights={{
    entities: { PERSON: 2, COMPANY: 5, PRODUCT: 3, LOCATION: 2 },
    relationships: { FOUNDED: 1, CEO_OF: 2, PRODUCES: 3, ... }
  }}
/>
```

### 5. API Client (`services/api.js`)

Centralized API communication layer.

**Available Methods:**

```javascript
// Build graph from text
api.buildGraph(text, sessionId)

// Upload PDF document
api.uploadPDF(file, sessionId)

// Get graph data for visualization
api.getGraphData(sessionId)

// Clear session graph
api.clearGraph(sessionId)

// Get insights
api.getInsights(sessionId)
```

**Configuration:**
```javascript
// Local development
const API_BASE_URL = 'http://localhost:8000';

// Production deployment
// const API_BASE_URL = 'https://your-backend.com';
```

## User Workflow

### 1. Text Input Flow

```
Enter Text → Click "Build Graph" → API Call → Loading State → Graph Renders
```

**Steps:**
1. User types or pastes text into input area
2. Clicks "Build Graph" button
3. Frontend calls `/build` endpoint
4. Loading spinner displays
5. Response received with entities and relationships
6. Graph visualization updates
7. Insights panel refreshes

### 2. PDF Upload Flow

```
Select PDF → Click Upload → File Processing → Text Extraction → Graph Building
```

**Steps:**
1. User clicks "Upload PDF" button
2. File selection dialog opens
3. User selects PDF file
4. Frontend sends file to `/upload` endpoint
5. Backend extracts text from PDF
6. NLP pipeline processes text
7. Graph updates with results

### 3. Graph Interaction Flow

```
Graph Rendered → User Clicks Node → Node Highlight → Related Edges Highlight
```

**Interactions:**
- Click and drag nodes to reposition
- Scroll to zoom in/out
- Hover over nodes for tooltips
- Click relationships for details

### 4. Session Management Flow

```
Initial Load → Generate Session ID → All Operations Tagged → Clear → New Session
```

**Session Lifecycle:**
1. Frontend generates unique session ID on load
2. All API calls include session ID
3. Backend stores graph data by session
4. User can clear session and start fresh
5. New session ID generated on clear

## Installation

### Prerequisites
- Node.js 18 or higher
- npm or yarn package manager

### Setup

1. Install dependencies:
```bash
npm install
```

2. Configure API endpoint:
Edit `src/services/api.js`:
```javascript
const API_BASE_URL = 'http://localhost:8000';
```

### Development

Run development server:
```bash
npm run dev
```

Application will be available at `http://localhost:5173`

### Production Build

Build optimized production bundle:
```bash
npm run build
```

Preview production build:
```bash
npm run preview
```

## Configuration

### Environment Variables

Create `.env` file (optional):
```env
VITE_API_URL=http://localhost:8000
```

Access in code:
```javascript
const apiUrl = import.meta.env.VITE_API_URL;
```

### Customization

**Change Graph Colors:**
Edit `GraphViewer.jsx`:
```javascript
const getNodeColor = (type) => {
  return {
    PERSON: '#YOUR_COLOR',
    ORG: '#YOUR_COLOR',
    // ...
  }[type];
};
```

**Adjust Graph Layout:**
```javascript
<ForceGraph2D
  graphData={graphData}
  nodeAutoColorBy="type"
  linkDirectionalArrowLength={6}
  linkDirectionalArrowRelPos={1}
  linkCurvature={0.2}  // Adjust curve
  d3VelocityDecay={0.3} // Adjust physics
/>
```

**Modify Input Limits:**
```javascript
<textarea
  maxLength={10000}  // Character limit
  rows={10}          // Visible rows
/>
```

## Component API

### App Component

```javascript
function App() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [sessionId, setSessionId] = useState(generateSessionId());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleBuildGraph = async (text) => {
    // Build graph from text
  };

  const handleFileUpload = async (file) => {
    // Process PDF upload
  };

  const handleClear = async () => {
    // Clear current graph
  };

  return (
    <div className="app">
      <InputPanel {...props} />
      <GraphViewer {...props} />
      <InsightsPanel {...props} />
    </div>
  );
}
```

### InputPanel Props

```typescript
interface InputPanelProps {
  onTextSubmit: (text: string) => Promise<void>;
  onFileUpload: (file: File) => Promise<void>;
  onClear: () => Promise<void>;
  loading: boolean;
}
```

### GraphViewer Props

```typescript
interface GraphViewerProps {
  graphData: {
    nodes: Array<{
      id: string;
      name: string;
      type: string;
      color?: string;
    }>;
    links: Array<{
      source: string;
      target: string;
      type: string;
      label?: string;
    }>;
  };
  loading: boolean;
}
```

## Styling

The application uses vanilla CSS with a modern, clean design.

**Key Style Features:**
- Responsive layout
- Flexbox-based grid system
- CSS variables for theming
- Smooth transitions
- Loading states

**CSS Variables:**
```css
:root {
  --primary-color: #4A90E2;
  --success-color: #50C878;
  --danger-color: #E74C3C;
  --background: #F5F7FA;
  --text-primary: #2C3E50;
  --border-radius: 8px;
  --box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}
```

## Error Handling

```javascript
// API error handling
try {
  const response = await api.buildGraph(text, sessionId);
  setGraphData(response);
} catch (error) {
  setError(error.message);
  console.error('Graph building failed:', error);
}

// Display error to user
{error && (
  <div className="error-message">
    {error}
  </div>
)}
```

## Performance

- **Initial Load:** <1s (optimized bundle)
- **Graph Render:** <500ms for 100 nodes
- **API Response:** <2s typical
- **Bundle Size:** ~200KB gzipped

**Optimization Techniques:**
- Code splitting with React.lazy()
- Memoization of expensive computations
- Debounced input handlers
- Lazy loading of graph library

## Testing

Run tests:
```bash
npm test
```

Test coverage:
```bash
npm run test:coverage
```

## Build Output

Production build creates:
```
dist/
├── index.html
├── assets/
│   ├── index-[hash].js
│   ├── index-[hash].css
│   └── vendor-[hash].js
└── favicon.ico
```

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Dependencies

```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "react-force-graph": "^1.43.0",
  "axios": "^1.6.0"
}
```

## Development Tools

```json
{
  "vite": "^5.0.0",
  "@vitejs/plugin-react": "^4.2.0",
  "eslint": "^8.55.0"
}
```

## Deployment

### Vercel
```bash
npm run build
vercel --prod
```

### Netlify
```bash
npm run build
netlify deploy --prod --dir=dist
```

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 5173
CMD ["npm", "run", "preview"]
```

## Troubleshooting

**Build Failed:**
- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node version: `node -v` (should be 18+)

**API Connection Failed:**
- Verify backend is running
- Check CORS settings in backend
- Verify API_BASE_URL in api.js

**Graph Not Rendering:**
- Check browser console for errors
- Verify graphData format
- Ensure react-force-graph is installed

**Slow Performance:**
- Limit graph nodes (<500 recommended)
- Use production build
- Enable browser caching

## Contributing

Follow these guidelines:
- Use functional components with hooks
- Write PropTypes or TypeScript interfaces
- Follow ESLint configuration
- Write tests for new features
- Update documentation

## License

MIT License
