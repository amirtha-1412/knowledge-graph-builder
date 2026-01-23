import './InsightsPanel.css';

const InsightsPanel = ({ insights }) => {
    if (!insights) {
        return (
            <div className="insights-panel">
                <h2>Graph Insights</h2>
                <p className="no-data">No insights available. Build a graph to see insights.</p>
            </div>
        );
    }

    return (
        <div className="insights-panel">
            <h2>Graph Insights</h2>

            <div className="insights-grid">
                <div className="insight-card">
                    <div className="insight-value">{insights.total_entities}</div>
                    <div className="insight-label">Total Entities</div>
                </div>

                <div className="insight-card">
                    <div className="insight-value">{insights.total_relationships}</div>
                    <div className="insight-label">Total Relationships</div>
                </div>

                {insights.avg_confidence && (
                    <div className="insight-card highlight">
                        <div className="insight-value">{(insights.avg_confidence * 100).toFixed(0)}%</div>
                        <div className="insight-label">Avg Confidence</div>
                    </div>
                )}

                {insights.most_connected_entity && (
                    <div className="insight-card highlight">
                        <div className="insight-value">{insights.most_connected_entity}</div>
                        <div className="insight-label">Most Connected Entity</div>
                    </div>
                )}
            </div>

            {insights.entity_types && Object.keys(insights.entity_types).length > 0 && (
                <div className="entity-types">
                    <h3>Entity Types Distribution</h3>
                    <div className="entity-types-list">
                        {Object.entries(insights.entity_types).map(([type, count]) => (
                            <div key={type} className="entity-type-item">
                                <span className="entity-type-name">{type}</span>
                                <span className="entity-type-count">{count}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default InsightsPanel;
