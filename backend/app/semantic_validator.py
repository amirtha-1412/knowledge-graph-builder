"""
Semantic Validator

This module provides validation logic for entities and relationships against extraction rules.
It ensures:
- Only allowed entity types are created
- Relationships follow semantic rules (correct entity type pairs)
- No hallucinated or invalid triples are persisted
"""

from typing import List, Tuple
from app.models import Entity, Relationship
from app.extraction_rules import (
    validate_relationship_semantics,
    AllowedEntityType,
    AllowedRelationshipType,
    SPACY_TO_NORMALIZED_ENTITY_TYPE
)

class SemanticValidator:
    """Validates entities and relationships against extraction rules"""
    
    @staticmethod
    def normalize_entity_type(spacy_type: str) -> str:
        """
        Convert SpaCy entity type to normalized type.
        
        Args:
            spacy_type: SpaCy NER label (e.g., "ORG", "GPE", "PERSON")
        
        Returns:
            Normalized entity type string or None if not allowed
        
        Example:
            >>> SemanticValidator.normalize_entity_type("ORG")
            "COMPANY"
            >>> SemanticValidator.normalize_entity_type("GPE")
            "LOCATION"
            >>> SemanticValidator.normalize_entity_type("DATE")
            None
        """
        entity_enum = SPACY_TO_NORMALIZED_ENTITY_TYPE.get(spacy_type)
        return entity_enum.value if entity_enum else None
    
    @staticmethod
    def validate_entity(entity: Entity) -> bool:
        """
        Validate if entity type is allowed.
        
        Args:
            entity: Entity object to validate
        
        Returns:
            True if valid, False if should be filtered out
        """
        normalized_type = SemanticValidator.normalize_entity_type(entity.type)
        return normalized_type is not None
    
    @staticmethod
    def validate_relationship(
        relationship: Relationship,
        entities: List[Entity]
    ) -> Tuple[bool, str]:
        """
        Validate if relationship follows semantic rules.
        
        Args:
            relationship: Relationship to validate
            entities: List of all entities for context
        
        Returns:
            (is_valid, reason) tuple
        
        Example:
            >>> entities = [
            ...     Entity(text="Steve Jobs", type="PERSON", ...),
            ...     Entity(text="Apple", type="ORG", ...)
            ... ]
            >>> rel = Relationship(source="Steve Jobs", target="Apple", type="FOUNDED", ...)
            >>> SemanticValidator.validate_relationship(rel, entities)
            (True, "Valid")
        """
        # Find source and target entity types
        source_entity = next((e for e in entities if e.text == relationship.source), None)
        target_entity = next((e for e in entities if e.text == relationship.target), None)
        
        if not source_entity or not target_entity:
            return False, "Source or target entity not found"
        
        # Normalize entity types
        source_type = SemanticValidator.normalize_entity_type(source_entity.type)
        target_type = SemanticValidator.normalize_entity_type(target_entity.type)
        
        if not source_type or not target_type:
            return False, f"Invalid entity types: {source_entity.type} or {target_entity.type}"
        
        # Validate relationship type exists
        try:
            AllowedRelationshipType(relationship.type)
        except ValueError:
            return False, f"Unknown relationship type: {relationship.type}"
        
        # Validate semantic correctness
        is_valid = validate_relationship_semantics(source_type, relationship.type, target_type)
        
        if not is_valid:
            return False, f"Invalid semantic triple: ({source_type})-[{relationship.type}]->({target_type})"
        
        return True, "Valid"
    
    @staticmethod
    def filter_entities(entities: List[Entity]) -> List[Entity]:
        """
        Filter entities to only allowed types.
        
        Args:
            entities: List of all extracted entities
        
        Returns:
            Filtered list of valid entities
        """
        valid_entities = []
        rejected_count = 0
        
        for entity in entities:
            if SemanticValidator.validate_entity(entity):
                valid_entities.append(entity)
            else:
                rejected_count += 1
                print(f"[Validator] Rejected entity: {entity.text} (type: {entity.type})")
        
        if rejected_count > 0:
            print(f"[Validator] Filtered {rejected_count} invalid entities, kept {len(valid_entities)}")
        
        return valid_entities
    
    @staticmethod
    def filter_relationships(
        relationships: List[Relationship],
        entities: List[Entity]
    ) -> List[Relationship]:
        """
        Filter relationships to only semantically valid ones.
        
        Args:
            relationships: List of all extracted relationships
            entities: List of all entities for context
        
        Returns:
            Filtered list of valid relationships
        """
        valid_relationships = []
        rejected_count = 0
        
        for rel in relationships:
            is_valid, reason = SemanticValidator.validate_relationship(rel, entities)
            if is_valid:
                valid_relationships.append(rel)
            else:
                rejected_count += 1
                print(f"[Validator] Rejected: {rel.source} -[{rel.type}]-> {rel.target} | Reason: {reason}")
        
        if rejected_count > 0:
            print(f"[Validator] Filtered {rejected_count} invalid relationships, kept {len(valid_relationships)}")
        
        return valid_relationships

if __name__ == "__main__":
    # Test validation
    from app.models import EntityCategory
    
    print("Testing Entity Validation:")
    valid_entity = Entity(
        text="Apple",
        type="ORG",
        category=EntityCategory.STRUCTURAL
    )
    invalid_entity = Entity(
        text="2024",
        type="DATE",
        category=EntityCategory.METADATA
    )
    
    print(f"Valid entity (Apple, ORG): {SemanticValidator.validate_entity(valid_entity)}")
    print(f"Invalid entity (2024, DATE): {SemanticValidator.validate_entity(invalid_entity)}")
    
    print("\nTesting Relationship Validation:")
    entities = [
        Entity(text="Steve Jobs", type="PERSON", category=EntityCategory.STRUCTURAL),
        Entity(text="Apple", type="ORG", category=EntityCategory.STRUCTURAL),
        Entity(text="Bill Gates", type="PERSON", category=EntityCategory.STRUCTURAL),
    ]
    
    valid_rel = Relationship(
        source="Steve Jobs",
        target="Apple",
        type="FOUNDED",
        reason="test"
    )
    
    invalid_rel = Relationship(
        source="Steve Jobs",
        target="Bill Gates",
        type="FOUNDED",
        reason="test"
    )
    
    print(f"Valid (PERSON → FOUNDED → COMPANY): {SemanticValidator.validate_relationship(valid_rel, entities)}")
    print(f"Invalid (PERSON → FOUNDED → PERSON): {SemanticValidator.validate_relationship(invalid_rel, entities)}")
