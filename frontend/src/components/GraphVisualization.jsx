import { useEffect, useRef, useState } from 'react';
import { Network } from 'vis-network';
import { api } from '../services/api';
import './GraphVisualization.css';

const GraphVisualization = ({ sessionId }) => {
    const containerRef = useRef(null);
    const networkRef = useRef(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [layoutType, setLayoutType] = useState('hierarchical');
    const [legendVisible, setLegendVisible] = useState(true);
    const [isFullscreen, setIsFullscreen] = useState(false);

    useEffect(() => {
        if (!containerRef.current || !sessionId) {
            return;
        }

        const loadGraphData = async () => {
            setLoading(true);
            setError(null);

            try {
                // Fetch graph data from secure backend endpoint
                const graphData = await api.getGraphData(sessionId);

                // Configure vis-network options with ENHANCED settings
                const options = {
                    nodes: {
                        shape: 'dot',
                        size: 50,  // INCREASED from 20 to 50
                        scaling: {
                            min: 30,
                            max: 80,
                            label: {
                                enabled: true,
                                min: 16,
                                max: 24
                            }
                        },
                        font: {
                            size: 18,  // INCREASED from 14 to 18
                            face: 'Inter, Arial, sans-serif',
                            color: '#1f2937',
                            bold: {
                                size: 20,
                                color: '#111827'
                            },
                            background: 'rgba(255, 255, 255, 0.9)',  // NEW: Label background
                            strokeWidth: 2,
                            strokeColor: '#fff'
                        },
                        borderWidth: 2,
                        borderWidthSelected: 4,
                        shadow: {
                            enabled: true,
                            color: 'rgba(0,0,0,0.2)',
                            size: 10,
                            x: 3,
                            y: 3
                        }
                    },
                    edges: {
                        arrows: {
                            to: {
                                enabled: true,
                                scaleFactor: 0.8,
                                type: 'arrow'
                            }
                        },
                        width: 4,  // INCREASED width for better visibility
                        color: {
                            color: '#64748b',
                            highlight: '#1e293b',
                            hover: '#334155',
                            opacity: 1.0
                        },
                        font: {
                            size: 12,
                            align: 'horizontal',
                            background: 'rgba(255, 255, 255, 0.95)',
                            strokeWidth: 3,
                            strokeColor: '#fff',
                            bold: true
                        },
                        smooth: {
                            type: 'cubicBezier',
                            forceDirection: layoutType === 'hierarchical' ? 'vertical' : 'none',
                            roundness: 0.5
                        },
                        color: {
                            inherit: false
                        },
                        chosen: {
                            edge: (values) => {
                                values.width = 5;
                            }
                        }
                    },
                    physics: {
                        enabled: layoutType !== 'hierarchical',
                        hierarchicalRepulsion: {
                            centralGravity: 0,
                            springLength: 200,
                            springConstant: 0.02,
                            nodeDistance: 250,  // INCREASED from 150
                            damping: 0.09,
                            avoidOverlap: 0.5
                        },
                        barnesHut: {
                            gravitationalConstant: -8000,
                            centralGravity: 0.3,
                            springLength: 200,
                            springConstant: 0.04,
                            damping: 0.09,
                            avoidOverlap: 0.2
                        },
                        stabilization: {
                            enabled: true,
                            iterations: 300,
                            updateInterval: 25
                        }
                    },
                    interaction: {
                        hover: true,
                        tooltipDelay: 100,
                        navigationButtons: true,
                        keyboard: true,
                        zoomView: true,
                        dragView: true
                    },
                    layout: {
                        improvedLayout: true,
                        hierarchical: layoutType === 'hierarchical' ? {
                            enabled: true,
                            direction: 'UD',  // Up-Down
                            sortMethod: 'directed',
                            levelSeparation: 200,
                            nodeSpacing: 250,  // INCREASED spacing
                            treeSpacing: 300,
                            blockShifting: true,
                            edgeMinimization: true,
                            parentCentralization: true
                        } : false
                    }
                };

                // Create the network
                if (networkRef.current) {
                    networkRef.current.destroy();
                }

                networkRef.current = new Network(
                    containerRef.current,
                    { nodes: graphData.nodes, edges: graphData.edges },
                    options
                );

                // Add event listeners
                networkRef.current.on('stabilizationIterationsDone', () => {
                    if (layoutType === 'hierarchical') {
                        networkRef.current.setOptions({ physics: false });
                    }
                });

            } catch (err) {
                console.error('Failed to load graph data:', err);
                setError('Failed to load graph visualization. Please try again.');
            } finally {
                setLoading(false);
            }
        };

        loadGraphData();

        return () => {
            if (networkRef.current) {
                networkRef.current.destroy();
                networkRef.current = null;
            }
        };
    }, [sessionId, layoutType]);

    // Control functions
    const handleFitToScreen = () => {
        if (networkRef.current) {
            networkRef.current.fit({
                animation: {
                    duration: 500,
                    easingFunction: 'easeInOutQuad'
                }
            });
        }
    };

    const handleZoomIn = () => {
        if (networkRef.current) {
            const scale = networkRef.current.getScale();
            networkRef.current.moveTo({
                scale: scale * 1.3,
                animation: {
                    duration: 300,
                    easingFunction: 'easeInOutQuad'
                }
            });
        }
    };

    const handleZoomOut = () => {
        if (networkRef.current) {
            const scale = networkRef.current.getScale();
            networkRef.current.moveTo({
                scale: scale * 0.7,
                animation: {
                    duration: 300,
                    easingFunction: 'easeInOutQuad'
                }
            });
        }
    };

    const handleResetLayout = () => {
        if (networkRef.current) {
            networkRef.current.setOptions({ physics: { enabled: true } });
            setTimeout(() => {
                networkRef.current.stabilize();
            }, 100);
        }
    };

    const handleLayoutChange = (e) => {
        setLayoutType(e.target.value);
    };

    const handleToggleFullscreen = () => {
        // Get the graph-container element itself
        const container = document.querySelector('.graph-container');
        if (!container) return;

        if (!document.fullscreenElement) {
            // Enter fullscreen
            container.requestFullscreen().then(() => {
                setIsFullscreen(true);
            }).catch((err) => {
                console.error('Error entering fullscreen:', err);
            });
        } else {
            // Exit fullscreen
            document.exitFullscreen().then(() => {
                setIsFullscreen(false);
            }).catch((err) => {
                console.error('Error exiting fullscreen:', err);
            });
        }
    };

    // Listen for fullscreen changes (e.g., ESC key)
    useEffect(() => {
        const handleFullscreenChange = () => {
            setIsFullscreen(!!document.fullscreenElement);
        };

        document.addEventListener('fullscreenchange', handleFullscreenChange);
        return () => {
            document.removeEventListener('fullscreenchange', handleFullscreenChange);
        };
    }, []);

    return (
        <div className="graph-container">
            {/* Interactive Controls */}
            <div className="graph-controls">
                <button onClick={handleToggleFullscreen} title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}>
                    {isFullscreen ? '🗗 Exit' : '⛶ Full'}
                </button>
                <button onClick={handleFitToScreen} title="Fit to Screen">
                    📐 Fit
                </button>
                <button onClick={handleZoomIn} title="Zoom In">
                    ➕ Zoom In
                </button>
                <button onClick={handleZoomOut} title="Zoom Out">
                    ➖ Zoom Out
                </button>
                <button onClick={handleResetLayout} title="Reset Layout">
                    🔄 Reset
                </button>
                <select
                    value={layoutType}
                    onChange={handleLayoutChange}
                    title="Change Layout"
                >
                    <option value="hierarchical">Hierarchical</option>
                    <option value="force">Force-Directed</option>
                </select>
            </div>

            {/* Legend Toggle Button */}
            <button
                className="legend-toggle"
                onClick={() => setLegendVisible(!legendVisible)}
                title={legendVisible ? "Hide Legend" : "Show Legend"}
            >
                {legendVisible ? '◀ Hide' : '▶ Legend'}
            </button>

            {/* Color Legend */}
            {legendVisible && (
                <div className="graph-legend">
                    <h4>Entity Types</h4>
                    <div className="legend-items">
                        <div className="legend-item">
                            <span className="color-dot" style={{ background: '#3b82f6' }}></span>
                            <span>PERSON</span>
                        </div>
                        <div className="legend-item">
                            <span className="color-dot" style={{ background: '#10b981' }}></span>
                            <span>ORGANIZATION</span>
                        </div>
                        <div className="legend-item">
                            <span className="color-dot" style={{ background: '#f59e0b' }}></span>
                            <span>LOCATION</span>
                        </div>
                        <div className="legend-item">
                            <span className="color-dot" style={{ background: '#ef4444' }}></span>
                            <span>DATE</span>
                        </div>
                        <div className="legend-item">
                            <span className="color-dot" style={{ background: '#8b5cf6' }}></span>
                            <span>PRODUCT</span>
                        </div>
                        <div className="legend-item">
                            <span className="color-dot" style={{ background: '#ec4899' }}></span>
                            <span>EVENT</span>
                        </div>
                        <div className="legend-item">
                            <span className="color-dot" style={{ background: '#14b8a6' }}></span>
                            <span>MONEY</span>
                        </div>
                        <div className="legend-item">
                            <span className="color-dot" style={{ background: '#f97316' }}></span>
                            <span>PERCENT</span>
                        </div>
                        <div className="legend-item">
                            <span className="color-dot" style={{ background: '#6366f1' }}></span>
                            <span>CARDINAL</span>
                        </div>
                        <div className="legend-item">
                            <span className="color-dot" style={{ background: '#84cc16' }}></span>
                            <span>ORDINAL</span>
                        </div>
                        <div className="legend-item">
                            <span className="color-dot" style={{ background: '#06b6d4' }}></span>
                            <span>FACILITY</span>
                        </div>
                        <div className="legend-item">
                            <span className="color-dot" style={{ background: '#a855f7' }}></span>
                            <span>WORK OF ART</span>
                        </div>
                    </div>
                </div>
            )}

            {loading && (
                <div className="graph-loading">
                    <div className="loading-spinner"></div>
                    <p>Loading graph visualization...</p>
                </div>
            )}
            {error && (
                <div className="graph-error">
                    <p>{error}</p>
                </div>
            )}
            <div
                ref={containerRef}
                className="graph-canvas"
                style={{ height: '700px', width: '100%' }}
            />
        </div>
    );
};

export default GraphVisualization;
