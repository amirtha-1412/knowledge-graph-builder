import { useEffect, useRef } from 'react';
import { Network } from 'vis-network';
import './GraphVisualization.css';

const GraphVisualization = ({ entities, relationships }) => {
    const containerRef = useRef(null);
    const networkRef = useRef(null);

    useEffect(() => {
        if (!containerRef.current || !entities || entities.length === 0) {
            return;
        }

        // Create nodes from entities
        const nodes = entities.map((entity, index) => ({
            id: index,
            label: entity.text,
            title: `Type: ${entity.type}`,
            color: getColorByType(entity.type),
            font: { color: '#ffffff' },
        }));

        // Create edges from relationships
        const edges = relationships.map((rel, index) => {
            const sourceIndex = entities.findIndex(e => e.text === rel.source);
            const targetIndex = entities.findIndex(e => e.text === rel.target);

            return {
                id: index,
                from: sourceIndex,
                to: targetIndex,
                label: rel.type,
                title: `Reason: ${rel.reason}`,
                arrows: 'to',
                font: { align: 'middle' },
            };
        });

        const data = { nodes, edges };

        const options = {
            nodes: {
                shape: 'dot',
                size: 20,
                borderWidth: 2,
                borderWidthSelected: 4,
            },
            edges: {
                width: 2,
                color: { color: '#848484', highlight: '#2B7CE9' },
                smooth: {
                    type: 'continuous',
                },
            },
            physics: {
                enabled: true,
                stabilization: {
                    iterations: 100,
                },
            },
            interaction: {
                hover: true,
                tooltipDelay: 100,
            },
        };

        // Destroy existing network if it exists
        if (networkRef.current) {
            networkRef.current.destroy();
        }

        // Create new network
        networkRef.current = new Network(containerRef.current, data, options);

        return () => {
            if (networkRef.current) {
                networkRef.current.destroy();
            }
        };
    }, [entities, relationships]);

    return (
        <div className="graph-container">
            <div ref={containerRef} className="graph-canvas" />
        </div>
    );
};

// Helper function to assign colors based on entity type
const getColorByType = (type) => {
    const colorMap = {
        PERSON: '#3498db',
        ORG: '#e74c3c',
        GPE: '#2ecc71',
        DATE: '#f39c12',
    };
    return colorMap[type] || '#95a5a6';
};

export default GraphVisualization;
