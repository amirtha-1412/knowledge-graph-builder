import { useState } from 'react';
import InputPanel from './components/InputPanel';
import GraphVisualization from './components/GraphVisualization';
import InsightsPanel from './components/InsightsPanel';
import { api } from './services/api';
import './App.css';

function App() {
  const [entities, setEntities] = useState([]);
  const [relationships, setRelationships] = useState([]);
  const [insights, setInsights] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleBuildGraph = async (text) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.buildGraph(text, sessionId);

      if (response.entities && response.relationships) {
        setEntities(response.entities);
        setRelationships(response.relationships);
        setSessionId(response.session_id);

        // Fetch insights
        const insightsData = await api.getInsights(response.session_id);
        setInsights(insightsData);
      }
    } catch (err) {
      setError('Failed to build graph. Please ensure the backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadPDF = async (file) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.uploadPDF(file, sessionId);

      if (response.entities && response.relationships) {
        setEntities(response.entities);
        setRelationships(response.relationships);
        setSessionId(response.session_id);

        // Fetch insights
        const insightsData = await api.getInsights(response.session_id);
        setInsights(insightsData);
      }
    } catch (err) {
      setError('Failed to process PDF. Please ensure the backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleClearGraph = async () => {
    if (sessionId) {
      try {
        await api.clearGraph(sessionId);
      } catch (err) {
        console.error('Failed to clear graph:', err);
      }
    }

    setEntities([]);
    setRelationships([]);
    setInsights(null);
    setSessionId(null);
    setError(null);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Enterprise Knowledge Graph Builder</h1>
        <p>Convert unstructured documents into explainable knowledge graphs</p>
      </header>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="app-content">
        <div className="left-panel">
          <InputPanel
            onBuildGraph={handleBuildGraph}
            onUploadPDF={handleUploadPDF}
            onClearGraph={handleClearGraph}
            loading={loading}
          />
          <InsightsPanel insights={insights} />
        </div>

        <div className="right-panel">
          <div className="graph-section">
            <h2>Knowledge Graph Visualization</h2>
            {entities.length > 0 ? (
              <GraphVisualization
                entities={entities}
                relationships={relationships}
              />
            ) : (
              <div className="empty-graph">
                <p>No graph data available. Enter text or upload a PDF to get started.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
