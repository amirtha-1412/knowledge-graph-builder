import spacy
from typing import List
from app.models import Entity

# Load SpaCy English model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import en_core_web_sm
    nlp = en_core_web_sm.load()

def extract_entities(text: str) -> List[Entity]:
    """
    Processes raw text to extract specific named entities (PERSON, ORG, GPE, DATE).
    """
    doc = nlp(text)
    entities = []
    
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG", "GPE", "DATE"]:
            entities.append(Entity(
                text=ent.text,
                type=ent.label_
            ))
            
    return entities

if __name__ == "__main__":
    sample_text = "Apple and Microsoft are tech giants based in California."
    print("Extracted Entities:")
    for e in extract_entities(sample_text):
        print(f" - {e.text} ({e.type})")
