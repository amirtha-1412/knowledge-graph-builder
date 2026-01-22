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
        Persists entities and relationships to Neo4j.
        Uses MERGE to avoid duplicate entities within the same session or globally.
        """
        with self.driver.session() as session:
            # 1. Create/Merge Entities
            for entity in entities:
                session.execute_write(self._merge_entity, entity, session_id)
            
            # 2. Create/Merge Relationships
            for rel in relationships:
                session.execute_write(self._merge_relationship, rel, session_id)

    @staticmethod
    def _merge_entity(tx, entity: Entity, session_id: str):
        # We use a generic 'Entity' label and a 'type' property
        query = (
            "MERGE (e:Entity {name: $name, type: $type}) "
            "ON CREATE SET e.session_id = $session_id, e.created_at = timestamp() "
            "RETURN e"
        )
        tx.run(query, name=entity.text, type=entity.type, session_id=session_id)

    @staticmethod
    def _merge_relationship(tx, rel: Relationship, session_id: str):
        # We find the source and target nodes and create a relationship
        # The relationship type is dynamic, so we use string interpolation for the label
        # (Be careful with string interpolation in Cypher, but here types are controlled by our logic)
        query = (
            f"MATCH (a:Entity {{name: $source}}), (b:Entity {{name: $target}}) "
            f"MERGE (a)-[r:{rel.type}]->(b) "
            "ON CREATE SET r.reason = $reason, r.session_id = $session_id, r.created_at = timestamp() "
            "RETURN r"
        )
        tx.run(query, source=rel.source, target=rel.target, reason=rel.reason, session_id=session_id)

    def clear_session(self, session_id: str):
        """Clears all nodes and relationships associated with a session_id."""
        with self.driver.session() as session:
            query = "MATCH (n {session_id: $session_id}) DETACH DELETE n"
            session.run(query, session_id=session_id)

    def get_insights(self, session_id: str) -> dict:
        """Fetches statistics for a specific session."""
        with self.driver.session() as session:
            # 1. Total entities and relationships
            stats_query = """
            MATCH (n {session_id: $session_id})
            WITH count(n) as node_count
            OPTIONAL MATCH (n {session_id: $session_id})-[r]->()
            RETURN node_count, count(r) as rel_count
            """
            stats = session.run(stats_query, session_id=session_id).single()
            
            # 2. Entity types distribution
            type_query = """
            MATCH (n:Entity {session_id: $session_id})
            RETURN n.type as type, count(n) as count
            """
            types_res = session.run(type_query, session_id=session_id)
            entity_types = {record["type"]: record["count"] for record in types_res}
            
            return {
                "total_entities": stats["node_count"] if stats else 0,
                "total_relationships": stats["rel_count"] if stats else 0,
                "most_connected_entity": None, # Complex query, optional for MVP
                "entity_types": entity_types
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
