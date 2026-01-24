# import spacy
# from typing import List, Tuple
# from app.models import Entity

# # Load SpaCy English model
# try:
#     nlp = spacy.load("en_core_web_sm")
# except OSError:
#     import en_core_web_sm
#     nlp = en_core_web_sm.load()
import spacy
from typing import List, Tuple
from app.models import Entity

# Load SpaCy English model (Render-safe)
nlp = spacy.load("en_core_web_sm")


# Increase max_length for large PDF documents (Aura DB & SpaCy support)
nlp.max_length = 2000000

def clean_text(text: str) -> str:
    """Removes noise and normalizes whitespace from PDF extractions."""
    import re
    # Replace multiple whitespaces/newlines with a single space
    cleaned = re.sub(r'\s+', ' ', text)
    return cleaned.strip()

def normalize_entity_name(text: str, entity_type: str) -> str:
    """
    Normalize entity names for deduplication.
    
    Examples:
    - "Apple Inc." -> "Apple"
    - "U.S." -> "United States"
    """
    normalized = text.strip()
    
    # Remove common suffixes for organizations
    if entity_type == "ORG":
        suffixes = [" Inc.", " Inc", " LLC", " Corp.", " Corporation", " Ltd.", " Co.", " Company"]
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()
    
    # Expand common abbreviations for locations
    if entity_type == "GPE":
        abbreviations = {
            "U.S.": "United States",
            "U.K.": "United Kingdom",
            "U.S.A.": "United States",
        }
        if normalized in abbreviations:
            normalized = abbreviations[normalized]
    
    return normalized

def extract_metadata(doc, document_id: str = None) -> dict:
    """
    Extract temporal and numeric metadata from document.
    These will be attached to relationships/events, not created as nodes.
    
    Returns: {
        'dates': [(text, context)],
        'money': [(text, context)],
        'percentages': [(text, context)],
        'quantities': [(text, context)]
    }
    """
    metadata = {
        'dates': [],
        'money': [],
        'percentages': [],
        'quantities': []
    }
    
    for ent in doc.ents:
        sent_text = ent.sent.text if ent.sent else ""
        
        if ent.label_ == "DATE":
            metadata['dates'].append((ent.text, sent_text))
        elif ent.label_ == "MONEY":
            metadata['money'].append((ent.text, sent_text))
        elif ent.label_ == "PERCENT":
            metadata['percentages'].append((ent.text, sent_text))
        elif ent.label_ in ["CARDINAL", "ORDINAL"]:
            metadata['quantities'].append((ent.text, sent_text))
    
    return metadata

def extract_entities(text: str, document_id: str = None) -> Tuple[List[Entity], dict]:
    """
    Processes raw text to extract STRUCTURAL entities only.
    Metadata (DATE, MONEY, PERCENT, etc.) is extracted separately for relationship enrichment.
    
    Returns:
        entities: List of structural entities (PERSON, ORG, GPE, PRODUCT, EVENT, FAC, WORK_OF_ART)
        metadata: Dict of temporal/numeric metadata for enrichment
    
    Supported structural entity types:
    - PERSON: People, including fictional
    - ORG: Companies, agencies, institutions
    - GPE: Countries, cities, states
    - PRODUCT: Objects, vehicles, foods, etc.
    - EVENT: Named hurricanes, battles, wars, sports events
    - FAC: Buildings, airports, highways, bridges
    - WORK_OF_ART: Titles of books, songs, etc.
    """
    from app.models import Entity, EntityCategory
    
    cleaned_text = clean_text(text)
    doc = nlp(cleaned_text)
    entities = []
    
    # Separate structural entities from metadata
    STRUCTURAL_TYPES = ["PERSON", "ORG", "GPE", "PRODUCT", "EVENT", "FAC", "WORK_OF_ART"]
    
    seen_entities = set()  # Deduplication
    
    for ent in doc.ents:
        if ent.label_ in STRUCTURAL_TYPES:
            # Normalize entity name
            normalized_name = normalize_entity_name(ent.text, ent.label_)
            
            # Create unique key for deduplication
            entity_key = (normalized_name.lower(), ent.label_)
            
            if entity_key not in seen_entities:
                seen_entities.add(entity_key)
                
                # Extract surrounding sentence for context
                sent_text = ent.sent.text if ent.sent else ""
                
                entities.append(Entity(
                    text=normalized_name,
                    type=ent.label_,
                    category=EntityCategory.STRUCTURAL,
                    start_char=ent.start_char,
                    end_char=ent.end_char,
                    context=sent_text[:200],  # Limit context to 200 chars
                    source_sentence=sent_text,
                    document_id=document_id
                ))
    
    # Extract metadata separately
    metadata = extract_metadata(doc, document_id)
    
    return entities, metadata

def extract_dependency_tree(text: str):
    """
    Extracts dependency tree for advanced relationship extraction.
    Used by relationship_logic.py for SVO patterns.
    """
    cleaned_text = clean_text(text)
    doc = nlp(cleaned_text)
    return doc

if __name__ == "__main__":
    sample_text = "Apple Inc. released the iPhone in 2007 for $599. The product sold 1 million units at the launch event."
    print("Extracted Structural Entities:")
    entities, metadata = extract_entities(sample_text)
    for e in entities:
        print(f" - {e.text} ({e.type}) | Context: {e.context[:50]}...")
    
    print("\nExtracted Metadata:")
    for key, values in metadata.items():
        if values:
            print(f" - {key}: {[v[0] for v in values]}")


