"""
Extraction Rules Configuration

This module defines the core rules for entity and relationship extraction:
- Allowed entity types (strict whitelist)
- Allowed relationship types (strict whitelist)
- Semantic validation rules for relationship triples

These rules enforce semantic correctness and prevent hallucinations.
"""

from enum import Enum
from typing import Dict, List, Tuple

class AllowedEntityType(str, Enum):
    """Strict whitelist of allowed entity types"""
    PERSON = "PERSON"
    COMPANY = "COMPANY"  # Maps from ORG
    PRODUCT = "PRODUCT"
    ORGANIZATION = "ORGANIZATION"  # Non-company orgs
    LOCATION = "LOCATION"  # Maps from GPE

class AllowedRelationshipType(str, Enum):
    """Strict whitelist of allowed relationships"""
    FOUNDED = "FOUNDED"
    CEO_OF = "CEO_OF"
    FORMER_CEO_OF = "FORMER_CEO_OF"
    EMPLOYED_BY = "EMPLOYED_BY"
    PRODUCES = "PRODUCES"
    RELEASED = "RELEASED"
    DEVELOPS = "DEVELOPS"
    OPERATES = "OPERATES"
    LOCATED_IN = "LOCATED_IN"
    HEADQUARTERED_IN = "HEADQUARTERED_IN"
    COLLABORATES_WITH = "COLLABORATES_WITH"
    COMPETES_WITH = "COMPETES_WITH"
    ACQUIRED = "ACQUIRED"

# Semantic validation rules: allowed (source_type, relationship, target_type) triples
SEMANTIC_RULES: Dict[AllowedRelationshipType, List[Tuple[AllowedEntityType, AllowedEntityType]]] = {
    AllowedRelationshipType.FOUNDED: [
        (AllowedEntityType.PERSON, AllowedEntityType.COMPANY),
    ],
    AllowedRelationshipType.CEO_OF: [
        (AllowedEntityType.PERSON, AllowedEntityType.COMPANY),
    ],
    AllowedRelationshipType.FORMER_CEO_OF: [
        (AllowedEntityType.PERSON, AllowedEntityType.COMPANY),
    ],
    AllowedRelationshipType.EMPLOYED_BY: [
        (AllowedEntityType.PERSON, AllowedEntityType.COMPANY),
        (AllowedEntityType.PERSON, AllowedEntityType.ORGANIZATION),
    ],
    AllowedRelationshipType.PRODUCES: [
        (AllowedEntityType.COMPANY, AllowedEntityType.PRODUCT),
    ],
    AllowedRelationshipType.RELEASED: [
        (AllowedEntityType.COMPANY, AllowedEntityType.PRODUCT),
    ],
    AllowedRelationshipType.DEVELOPS: [
        (AllowedEntityType.COMPANY, AllowedEntityType.PRODUCT),
    ],
    AllowedRelationshipType.OPERATES: [
        (AllowedEntityType.COMPANY, AllowedEntityType.ORGANIZATION),
    ],
    AllowedRelationshipType.LOCATED_IN: [
        (AllowedEntityType.COMPANY, AllowedEntityType.LOCATION),
        (AllowedEntityType.ORGANIZATION, AllowedEntityType.LOCATION),
    ],
    AllowedRelationshipType.HEADQUARTERED_IN: [
        (AllowedEntityType.COMPANY, AllowedEntityType.LOCATION),
    ],
    AllowedRelationshipType.COMPETES_WITH: [
        (AllowedEntityType.COMPANY, AllowedEntityType.COMPANY),
    ],
    AllowedRelationshipType.COLLABORATES_WITH: [
        (AllowedEntityType.COMPANY, AllowedEntityType.COMPANY),
    ],
    AllowedRelationshipType.ACQUIRED: [
        (AllowedEntityType.COMPANY, AllowedEntityType.COMPANY),
    ],
}

# Entity type mapping from SpaCy to our normalized types
SPACY_TO_NORMALIZED_ENTITY_TYPE = {
    "PERSON": AllowedEntityType.PERSON,
    "ORG": AllowedEntityType.COMPANY,  # Default ORG mapped to COMPANY
    "GPE": AllowedEntityType.LOCATION,
    "PRODUCT": AllowedEntityType.PRODUCT,
}

def validate_relationship_semantics(
    source_entity_type: str,
    relationship_type: str,
    target_entity_type: str
) -> bool:
    """
    Validates if a relationship triple follows semantic rules.
    
    Args:
        source_entity_type: Normalized entity type (e.g., "COMPANY")
        relationship_type: Relationship type (e.g., "FOUNDED")
        target_entity_type: Normalized entity type (e.g., "PERSON")
    
    Returns:
        True if valid, False otherwise
    
    Example:
        >>> validate_relationship_semantics("PERSON", "FOUNDED", "COMPANY")
        True
        >>> validate_relationship_semantics("PERSON", "FOUNDED", "PERSON")
        False
    """
    try:
        rel_enum = AllowedRelationshipType(relationship_type)
        source_enum = AllowedEntityType(source_entity_type)
        target_enum = AllowedEntityType(target_entity_type)
        
        allowed_pairs = SEMANTIC_RULES.get(rel_enum, [])
        return (source_enum, target_enum) in allowed_pairs
    except (ValueError, KeyError):
        return False

def get_allowed_entity_types() -> List[str]:
    """Returns list of all allowed entity types"""
    return [e.value for e in AllowedEntityType]

def get_allowed_relationship_types() -> List[str]:
    """Returns list of all allowed relationship types"""
    return [r.value for r in AllowedRelationshipType]

if __name__ == "__main__":
    # Test validation
    print("Testing semantic validation:")
    print(f"PERSON → FOUNDED → COMPANY: {validate_relationship_semantics('PERSON', 'FOUNDED', 'COMPANY')}")
    print(f"PERSON → FOUNDED → PERSON: {validate_relationship_semantics('PERSON', 'FOUNDED', 'PERSON')}")
    print(f"COMPANY → PRODUCES → PRODUCT: {validate_relationship_semantics('COMPANY', 'PRODUCES', 'PRODUCT')}")
    print(f"PERSON → PRODUCES → PRODUCT: {validate_relationship_semantics('PERSON', 'PRODUCES', 'PRODUCT')}")
    
    print(f"\nAllowed entity types: {get_allowed_entity_types()}")
    print(f"Allowed relationship types: {get_allowed_relationship_types()}")
