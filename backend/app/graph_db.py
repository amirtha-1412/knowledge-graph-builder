from neo4j import GraphDatabase
from app.config import get_settings
from app.models import Entity, Relationship
from typing import List
import uuid

settings = get_settings()

class Neo4jManager:
    def __init__(self):
        print("Neo4jManager: Connecting to Aura DB...")
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri, 
            auth=(settings.neo4j_user, settings.neo4j_password),
            max_connection_lifetime=30 * 60, # 30 minutes
            max_connection_pool_size=50,
            connection_timeout=30.0,
            liveness_check_timeout=10.0
        )
        self.initialize_schema()

    def verify_connectivity(self):
        """Verifies if the driver can connect to the server."""
        try:
            self.driver.verify_connectivity()
            return True
        except Exception as e:
            print(f"Neo4j Connectivity Error: {e}")
            return False

    def close(self):
        self.driver.close()

    def initialize_schema(self):
        """
        Sets up the graph schema by creating constraints and indexes.
        Ensures entity names are unique for their type.
        """
        with self.driver.session() as session:
            # Create uniqueness constraint for Entities based on name and type
            # In Neo4j 5.x+, the syntax is IS UNIQUE
            try:
                session.run("CREATE CONSTRAINT entity_unique_name IF NOT EXISTS FOR (e:Entity) REQUIRE (e.name, e.type) IS UNIQUE")
                print("Schema: Constraint created (or already exists).")
            except Exception as e:
                print(f"Schema Warning: Could be using Neo4j < 5.0 or lack permissions: {e}")
                # Fallback for older versions if necessary, but Aura is usually 5.x

    def save_graph_data(self, session_id: str, entities: List[Entity], relationships: List[Relationship]):
        """
        Persists entities and relationships to Neo4j atomically.
        """
        with self.driver.session() as session:
            session.execute_write(self._persist_all, entities, relationships, session_id)

    @staticmethod
    def _persist_all(tx, entities: List[Entity], relationships: List[Relationship], session_id: str):
        # 1. Merge all entities first
        for entity in entities:
            Neo4jManager._merge_entity(tx, entity, session_id)
        
        # 2. Merge all relationships
        for rel in relationships:
            Neo4jManager._merge_relationship(tx, rel, session_id)

    @staticmethod
    def _merge_entity(tx, entity: Entity, session_id: str):
        # We use a generic 'Entity' label and a 'type' property
        query = (
            "MERGE (e:Entity {name: $name, type: $type}) "
            "ON CREATE SET e.created_at = timestamp() "
            "SET e.session_id = $session_id, e.updated_at = timestamp() "
            "RETURN e"
        )
        tx.run(query, name=entity.text, type=entity.type, session_id=session_id)

    @staticmethod
    def _merge_relationship(tx, rel: Relationship, session_id: str):
        # Match by name AND the current session_id to ensure we link current entities
        query = (
            f"MATCH (a:Entity {{name: $source, session_id: $session_id}}), "
            f"      (b:Entity {{name: $target, session_id: $session_id}}) "
            f"MERGE (a)-[r:{rel.type}]->(b) "
            "ON CREATE SET r.created_at = timestamp() "
            "SET r.reason = $reason, r.confidence = $confidence, r.verb = $verb, r.session_id = $session_id, r.updated_at = timestamp() "
            "RETURN r"
        )
        tx.run(query, source=rel.source, target=rel.target, reason=rel.reason, 
               confidence=rel.confidence, verb=rel.verb, session_id=session_id)

    def clear_session(self, session_id: str):
        """Clears all nodes and relationships associated with a session_id."""
        with self.driver.session() as session:
            query = "MATCH (n {session_id: $session_id}) DETACH DELETE n"
            session.run(query, session_id=session_id)

    def get_insights(self, session_id: str) -> dict:
        """Fetches statistics for a specific session with robust counting."""
        with self.driver.session() as session:
            # 1. Total entities and relationships (Combined and robust)
            stats_query = """
            MATCH (n:Entity {session_id: $session_id})
            WITH count(DISTINCT n) as node_count
            OPTIONAL MATCH ()-[r {session_id: $session_id}]->()
            RETURN node_count, count(DISTINCT r) as rel_count, avg(r.confidence) as avg_conf
            """
            result = session.run(stats_query, session_id=session_id).single()
            
            # 2. Entity types distribution
            type_query = """
            MATCH (n:Entity {session_id: $session_id})
            RETURN n.type as type, count(DISTINCT n) as count
            """
            types_res = session.run(type_query, session_id=session_id)
            entity_types = {record["type"]: record["count"] for record in types_res}
            
            return {
                "total_entities": result["node_count"] if result else 0,
                "total_relationships": result["rel_count"] if result else 0,
                "most_connected_entity": None,
                "entity_types": entity_types,
                "avg_confidence": round(result["avg_conf"], 2) if result and result["avg_conf"] else None
            }
    
    def get_graph_visualization_data(self, session_id: str) -> dict:
        """Returns graph data formatted for vis-network visualization."""
        with self.driver.session() as session:
            # Query for nodes
            nodes_query = """
            MATCH (n:Entity {session_id: $session_id})
            RETURN n.name as label, n.type as group, id(n) as id
            """
            nodes_result = session.run(nodes_query, session_id=session_id)
            
            # Color mapping for entity types
            color_map = {
                "PERSON": "#3b82f6",      # Blue
                "ORG": "#10b981",         # Green
                "GPE": "#f59e0b",         # Orange
                "DATE": "#ef4444",        # Red
                "PRODUCT": "#8b5cf6",     # Purple
                "EVENT": "#ec4899",       # Pink
                "MONEY": "#14b8a6",       # Teal
                "PERCENT": "#f97316",     # Dark Orange
                "CARDINAL": "#6366f1",    # Indigo
                "ORDINAL": "#84cc16",     # Lime
                "FAC": "#06b6d4",         # Cyan
                "WORK_OF_ART": "#a855f7"  # Purple
            }
            
            nodes = []
            for record in nodes_result:
                nodes.append({
                    "id": record["id"],
                    "label": record["label"],
                    "group": record["group"],
                    "color": color_map.get(record["group"], "#6b7280"),
                    "title": f"{record['label']} ({record['group']})"  # Tooltip
                })
            
            # Query for edges
            edges_query = """
            MATCH (n1:Entity {session_id: $session_id})-[r]->(n2:Entity {session_id: $session_id})
            RETURN id(n1) as from, id(n2) as to, type(r) as label, 
                   r.confidence as confidence, r.reason as title
            """
            edges_result = session.run(edges_query, session_id=session_id)
            
            edges = []
            for record in edges_result:
                confidence = record["confidence"] if record["confidence"] else 1.0
                edges.append({
                    "from": record["from"],
                    "to": record["to"],
                    "label": record["label"],
                    "title": record["title"],  # Tooltip with reason
                    "width": max(1, confidence * 3),  # Width based on confidence
                    "color": {
                        "opacity": confidence  # Opacity based on confidence
                    }
                })
            
            return {
                "nodes": nodes,
                "edges": edges
            }

# Initialize a global manager instance
graph_manager = Neo4jManager()

if __name__ == "__main__":
    # Test persistence
    test_session = f"test-{uuid.uuid4().hex[:6]}"
    test_entities = [
        Entity(text="Google", type="ORG"),
        Entity(text="Sundar Pichai", type="PERSON")
    ]
    test_relationships = [
        Relationship(
            source="Sundar Pichai", 
            target="Google", 
            type="WORKS_AT", 
            reason="Sundar Pichai and Google detected in same sentence"
        )
    ]
    
    print(f"Testing graph persistence for session: {test_session}...")
    try:
        graph_manager.save_graph_data(test_session, test_entities, test_relationships)
        print("Success! Data persisted to Neo4j.")
        # Cleanup
        # graph_manager.clear_session(test_session)
        # print("Test session cleaned up.")
    except Exception as e:
        print(f"Persistence Failed: {e}")
    finally:
        graph_manager.close()
