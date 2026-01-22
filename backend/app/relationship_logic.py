import spacy
from typing import List
from app.models import Relationship

# Load SpaCy English model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import en_core_web_sm
    nlp = en_core_web_sm.load()

def infer_relationships(text: str) -> List[Relationship]:
    """
    Infers relationships between entities using rule-based logic.
    Each relationship includes a 'reason' for explainability.
    
    Rules:
    - WORKS_AT: PERSON and ORG in the same sentence
    - LOCATED_IN: ORG and GPE in the same sentence
    """
    doc = nlp(text)
    relationships = []
    
    for sent in doc.sents:
        entities = [(ent.text, ent.label_) for ent in sent.ents]
        
        # Identity types
        persons = [e[0] for e in entities if e[1] == "PERSON"]
        orgs = [e[0] for e in entities if e[1] == "ORG"]
        gpes = [e[0] for e in entities if e[1] == "GPE"]
        
        # Rule 1: WORKS_AT (PERSON + ORG)
        for person in persons:
            for org in orgs:
                relationships.append(Relationship(
                    source=person,
                    target=org,
                    type="WORKS_AT",
                    reason=f"PERSON ({person}) and ORG ({org}) detected in the same sentence."
                ))
        
        # Rule 2: LOCATED_IN (ORG + GPE)
        for org in orgs:
            for gpe in gpes:
                relationships.append(Relationship(
                    source=org,
                    target=gpe,
                    type="LOCATED_IN",
                    reason=f"ORG ({org}) and GPE ({gpe}) detected in the same sentence."
                ))
                
    return relationships

if __name__ == "__main__":
    sample_text = "Elon Musk works at Tesla. Tesla is located in California."
    print("Inferred Relationships:")
    for r in infer_relationships(sample_text):
        print(f" - {r.source} {r.type} {r.target} | Reason: {r.reason}")
