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

    def save_graph_data(self, session_id: str, entities: List[Entity], relationships: List[Relationship], events: List = None):
        """
        Persists entities, relationships, and events to Neo4j atomically.
        Only STRUCTURAL entities are persisted as nodes.
        """
        with self.driver.session() as session:
            session.execute_write(self._persist_all, entities, relationships, events or [], session_id)

    @staticmethod
    def _persist_all(tx, entities: List[Entity], relationships: List[Relationship], events: List, session_id: str):
        from app.models import EntityCategory
        
        # 1. Merge all STRUCTURAL entities only (filter out METADATA entities)
        for entity in entities:
            if entity.category == EntityCategory.STRUCTURAL:
                Neo4jManager._merge_entity(tx, entity, session_id)
        
        # 2. Merge all events
        for event in events:
            Neo4jManager._merge_event(tx, event, session_id)
        
        # 3. Merge all relationships
        for rel in relationships:
            Neo4jManager._merge_relationship(tx, rel, session_id)

    @staticmethod
    def _merge_entity(tx, entity: Entity, session_id: str):
        """
        Merge a STRUCTURAL entity into Neo4j.
        Stores document traceability information.
        """
        query = (
            "MERGE (e:Entity {name: $name, type: $type}) "
            "ON CREATE SET e.created_at = timestamp() "
            "SET e.session_id = $session_id, e.updated_at = timestamp(), "
            "e.document_id = $document_id, e.source_sentence = $source_sentence "
            "RETURN e"
        )
        tx.run(query, name=entity.text, type=entity.type, session_id=session_id,
               document_id=entity.document_id, source_sentence=entity.source_sentence)
    
    @staticmethod
    def _merge_event(tx, event, session_id: str):
        """
        Merge an Event node into Neo4j.
        Events are temporal, transaction-based facts (e.g., acquisitions, launches).
        """
        query = (
            "MERGE (e:Event {name: $name, type: $event_type}) "
            "ON CREATE SET e.created_at = timestamp() "
            "SET e.session_id = $session_id, e.date = $date, "
            "e.location = $location, e.amount = $amount, e.context = $context, "
            "e.document_id = $document_id, e.confidence = $confidence, "
            "e.updated_at = timestamp() "
            "RETURN e"
        )
        tx.run(query, name=event.name, event_type=event.event_type.value,
               session_id=session_id, date=event.date, location=event.location,
               amount=event.amount, context=event.context,
               document_id=event.document_id, confidence=event.confidence)
        
        # Link event to participants
        for participant in event.participants:
            link_query = (
                "MATCH (event:Event {name: $event_name, session_id: $session_id}), "
                "      (entity:Entity {name: $participant, session_id: $session_id}) "
                "MERGE (event)-[r:INVOLVES]->(entity) "
                "SET r.created_at = timestamp() "
                "RETURN r"
            )
            tx.run(link_query, event_name=event.name, participant=participant, session_id=session_id)

    @staticmethod
    def _merge_relationship(tx, rel: Relationship, session_id: str):
        """
        Merge a relationship into Neo4j.
        Attaches temporal/monetary metadata as relationship properties (not as nodes).
        """
        # Extract metadata for relationship properties
        date_val = rel.metadata.get('date') if rel.metadata else None
        amount_val = rel.metadata.get('amount') if rel.metadata else None
        
        query = (
            f"MATCH (a:Entity {{name: $source, session_id: $session_id}}), "
            f"      (b:Entity {{name: $target, session_id: $session_id}}) "
            f"MERGE (a)-[r:{rel.type}]->(b) "
            "ON CREATE SET r.created_at = timestamp() "
            "SET r.reason = $reason, r.confidence = $confidence, r.verb = $verb, "
            "r.date = $date, r.amount = $amount, "
            "r.source_sentence = $source_sentence, r.document_id = $document_id, "
            "r.session_id = $session_id, r.updated_at = timestamp() "
            "RETURN r"
        )
        tx.run(query, source=rel.source, target=rel.target, reason=rel.reason,
               confidence=rel.confidence, verb=rel.verb, session_id=session_id,
               date=date_val, amount=amount_val,
               source_sentence=rel.source_sentence, document_id=rel.document_id)

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
        """
        Returns graph data formatted for vis-network visualization.
        Includes both Entity and Event nodes.
        """
        with self.driver.session() as session:
            # Query for Entity nodes
            entity_nodes_query = """
            MATCH (n:Entity {session_id: $session_id})
            RETURN n.name as label, n.type as group, id(n) as id, 
                   n.source_sentence as source, 'Entity' as node_type
            """
            entity_nodes_result = session.run(entity_nodes_query, session_id=session_id)
            
            # Query for Event nodes
            event_nodes_query = """
            MATCH (n:Event {session_id: $session_id})
            RETURN n.name as label, n.type as group, id(n) as id,
                   n.context as source, 'Event' as node_type, 
                   n.date as date, n.amount as amount
            """
            event_nodes_result = session.run(event_nodes_query, session_id=session_id)
            
            # Color mapping for entity types
            color_map = {
                "PERSON": "#3b82f6",      # Blue
                "ORG": "#10b981",         # Green
                "GPE": "#f59e0b",         # Orange
                "PRODUCT": "#8b5cf6",     # Purple
                "FAC": "#06b6d4",         # Cyan
                "WORK_OF_ART": "#a855f7", # Purple
                # Event types
                "Acquisition": "#fbbf24",     # Amber
                "ProductLaunch": "#ec4899",   # Pink
                "LeadershipChange": "#f59e0b", # Orange
                "Conference": "#8b5cf6",      # Purple
                "FundingRound": "#10b981",    # Green
                "Other": "#6b7280"            # Gray
            }
            
            nodes = []
            
            # Add Entity nodes
            for record in entity_nodes_result:
                tooltip = f"{record['label']} ({record['group']})"
                if record.get('source'):
                    tooltip += f"\n\nSource: {record['source'][:100]}..."
                
                nodes.append({
                    "id": record["id"],
                    "label": record["label"],
                    "group": record["group"],
                    "color": color_map.get(record["group"], "#6b7280"),
                    "title": tooltip,
                    "shape": "dot"  # Circle for entities
                })
            
            # Add Event nodes
            for record in event_nodes_result:
                tooltip = f"EVENT: {record['label']}\nType: {record['group']}"
                if record.get('date'):
                    tooltip += f"\nDate: {record['date']}"
                if record.get('amount'):
                    tooltip += f"\nAmount: {record['amount']}"
                if record.get('source'):
                    tooltip += f"\n\nContext: {record['source'][:100]}..."
                
                nodes.append({
                    "id": record["id"],
                    "label": record["label"],
                    "group": record["group"],
                    "color": color_map.get(record["group"], "#fbbf24"),
                    "title": tooltip,
                    "shape": "diamond",  # Diamond for events
                    "size": 35  # Slightly larger
                })
            
            # Query for relationships between entities
            edges_query = """
            MATCH (n1 {session_id: $session_id})-[r]->(n2 {session_id: $session_id})
            RETURN id(n1) as from, id(n2) as to, type(r) as label, 
                   r.confidence as confidence, r.reason as reason,
                   r.date as date, r.amount as amount, r.source_sentence as source
            """
            edges_result = session.run(edges_query, session_id=session_id)
            
            edges = []
            for record in edges_result:
                confidence = record["confidence"] if record["confidence"] else 1.0
                
                # Build enhanced tooltip
                tooltip = f"{record['label']}"
                if record.get('date'):
                    tooltip += f"\nDate: {record['date']}"
                if record.get('amount'):
                    tooltip += f"\nAmount: {record['amount']}"
                if confidence:
                    tooltip += f"\nConfidence: {confidence:.2f}"
                if record.get('reason'):
                    tooltip += f"\n\n{record['reason'][:150]}..."
                
                edges.append({
                    "from": record["from"],
                    "to": record["to"],
                    "label": record["label"],
                    "title": tooltip,
                    "width": max(2, confidence * 4),  # Width based on confidence
                    "color": {
                        "color": "#64748b",
                        "opacity": min(1.0, confidence + 0.3)  # Opacity based on confidence
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
