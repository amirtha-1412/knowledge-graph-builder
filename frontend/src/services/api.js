const API_BASE_URL = 'http://localhost:8000';

export const api = {
  buildGraph: async (text, sessionId = null) => {
    const response = await fetch(`${API_BASE_URL}/build`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text, session_id: sessionId }),
    });
    return response.json();
  },

  uploadPDF: async (file, sessionId = null) => {
    const formData = new FormData();
    formData.append('file', file);
    if (sessionId) {
      formData.append('session_id', sessionId);
    }
    
    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });
    return response.json();
  },

  clearGraph: async (sessionId) => {
    const response = await fetch(`${API_BASE_URL}/clear?session_id=${sessionId}`, {
      method: 'DELETE',
    });
    return response.json();
  },

  getInsights: async (sessionId) => {
    const response = await fetch(`${API_BASE_URL}/insights?session_id=${sessionId}`);
    return response.json();
  },

  getGraphData: async (sessionId) => {
    const response = await fetch(`${API_BASE_URL}/graph-data?session_id=${sessionId}`);
    return response.json();
  },
};
