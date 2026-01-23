import spacy
from typing import List
from app.models import Entity

# Load SpaCy English model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import en_core_web_sm
    nlp = en_core_web_sm.load()

# Increase max_length for large PDF documents (Aura DB & SpaCy support)
nlp.max_length = 2000000

def clean_text(text: str) -> str:
    """Removes noise and normalizes whitespace from PDF extractions."""
    import re
    # Replace multiple whitespaces/newlines with a single space
    cleaned = re.sub(r'\s+', ' ', text)
    return cleaned.strip()

def extract_entities(text: str) -> List[Entity]:
    """
    Processes raw text to extract enhanced set of named entities.
    
    Supported entity types:
    - PERSON: People, including fictional
    - ORG: Companies, agencies, institutions
    - GPE: Countries, cities, states
    - DATE: Absolute or relative dates or periods
    - PRODUCT: Objects, vehicles, foods, etc.
    - EVENT: Named hurricanes, battles, wars, sports events
    - MONEY: Monetary values, including unit
    - PERCENT: Percentage, including "%"
    - CARDINAL: Numerals that do not fall under another type
    - ORDINAL: "first", "second", etc.
    - FAC: Buildings, airports, highways, bridges
    - WORK_OF_ART: Titles of books, songs, etc.
    """
    cleaned_text = clean_text(text)
    doc = nlp(cleaned_text)
    entities = []
    
    # Expanded entity types for better knowledge graph
    supported_types = [
        "PERSON", "ORG", "GPE", "DATE", "PRODUCT", "EVENT",
        "MONEY", "PERCENT", "CARDINAL", "ORDINAL", "FAC", 
        "WORK_OF_ART"
    ]
    
    seen_entities = set()  # Deduplication
    
    for ent in doc.ents:
        if ent.label_ in supported_types:
            # Create unique key for deduplication
            entity_key = (ent.text.lower(), ent.label_)
            
            if entity_key not in seen_entities:
                seen_entities.add(entity_key)
                
                # Extract surrounding sentence for context
                sent_text = ent.sent.text if ent.sent else ""
                
                entities.append(Entity(
                    text=ent.text,
                    type=ent.label_,
                    start_char=ent.start_char,
                    end_char=ent.end_char,
                    context=sent_text[:200]  # Limit context to 200 chars
                ))
    
    return entities

def extract_dependency_tree(text: str):
    """
    Extracts dependency tree for advanced relationship extraction.
    Used by relationship_logic.py for SVO patterns.
    """
    cleaned_text = clean_text(text)
    doc = nlp(cleaned_text)
    return doc

if __name__ == "__main__":
    sample_text = "Apple released the iPhone in 2007 for $599. The product sold 1 million units at the launch event."
    print("Extracted Entities:")
    for e in extract_entities(sample_text):
        print(f" - {e.text} ({e.type}) | Context: {e.context[:50]}...")

