import spacy
from typing import List, Tuple
from app.models import Relationship
from app.nlp_engine import clean_text, extract_dependency_tree

# Load SpaCy English model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import en_core_web_sm
    nlp = en_core_web_sm.load()

# Match the max_length set in nlp_engine.py
nlp.max_length = 2000000

# Verb mappings for relationship inference
VERB_TO_RELATIONSHIP = {
    # Ownership & Control
    "own": "OWNS",
    "owns": "OWNS",
    "possess": "OWNS",
    "control": "CONTROLS",
    "controls": "CONTROLS",
    
    # Work relationships
    "work": "WORKS_AT",
    "works": "WORKS_AT",
    "employ": "EMPLOYS",
    "employs": "EMPLOYS",
    "hire": "EMPLOYS",
    "hired": "EMPLOYS",
    
    # Location relationships
    "locate": "LOCATED_IN",
    "located": "LOCATED_IN",
    "base": "LOCATED_IN",
    "based": "LOCATED_IN",
    "headquarter": "HEADQUARTERED_IN",
    "headquartered": "HEADQUARTERED_IN",
    
    # Hierarchical relationships
    "acquire": "ACQUIRED_BY",
    "acquired": "ACQUIRED_BY",
    "buy": "ACQUIRED_BY",
    "bought": "ACQUIRED_BY",
    "purchase": "ACQUIRED_BY",
    "purchased": "ACQUIRED_BY",
    
    # Production relationships
    "produce": "PRODUCES",
    "produces": "PRODUCES",
    "manufacture": "PRODUCES",
    "manufactures": "PRODUCES",
    "make": "PRODUCES",
    "makes": "PRODUCES",
    "create": "CREATES",
    "creates": "CREATES",
    "develop": "DEVELOPS",
    "develops": "DEVELOPS",
    "build": "BUILDS",
    "builds": "BUILDS",
    "release": "RELEASED",
    "released": "RELEASED",
    "launch": "LAUNCHED",
    "launched": "LAUNCHED",
    
    # Temporal relationships
    "found": "FOUNDED_IN",
    "founded": "FOUNDED_IN",
    "establish": "ESTABLISHED_IN",
    "established": "ESTABLISHED_IN",
    "occur": "OCCURRED_ON",
    "occurred": "OCCURRED_ON",
    "happen": "OCCURRED_ON",
    "happened": "OCCURRED_ON",
    
    # Collaboration & Competition
    "collaborate": "COLLABORATES_WITH",
    "collaborates": "COLLABORATES_WITH",
    "partner": "PARTNERS_WITH",
    "partners": "PARTNERS_WITH",
    "compete": "COMPETES_WITH",
    "competes": "COMPETES_WITH",
    "rival": "COMPETES_WITH",
    "rivals": "COMPETES_WITH",
}

def calculate_confidence(entity1_text: str, entity2_text: str, verb: str, sentence: str) -> float:
    """
    Calculate confidence score for a relationship based on various factors.
    
    Factors:
    - Verb specificity (e.g., "acquired" is more specific than "has")
    - Distance between entities in sentence
    - Presence of strong indicators (e.g., "CEO of", "founded by")
    """
    confidence = 0.5  # Base confidence
    
    # High confidence verbs
    high_confidence_verbs = ["acquired", "founded", "owns", "produces", "headquartered"]
    if verb.lower() in high_confidence_verbs:
        confidence += 0.3
    
    # Check for strong indicators in sentence
    strong_indicators = [
        "CEO of", "founder of", "president of", "director of",
        "acquired by", "owned by", "produced by", "developed by",
        "part of", "subsidiary of", "division of"
    ]
    
    for indicator in strong_indicators:
        if indicator.lower() in sentence.lower():
            confidence += 0.2
            break
    
    # Distance penalty (entities far apart = lower confidence)
    entity1_pos = sentence.lower().find(entity1_text.lower())
    entity2_pos = sentence.lower().find(entity2_text.lower())
    
    if entity1_pos != -1 and entity2_pos != -1:
        distance = abs(entity1_pos - entity2_pos)
        if distance < 30:
            confidence += 0.2
        elif distance > 100:
            confidence -= 0.1
    
    # Ensure confidence is between 0 and 1
    return max(0.0, min(1.0, confidence))

def extract_svo_relationships(text: str) -> List[Relationship]:
    """
    Extract relationships using Subject-Verb-Object (SVO) parsing.
    Uses SpaCy dependency parsing to find (nsubj, ROOT, dobj/pobj) patterns.
    """
    doc = extract_dependency_tree(text)
    relationships = []
    
    for sent in doc.sents:
        # Find verb roots in the sentence
        for token in sent:
            if token.pos_ == "VERB" and token.dep_ == "ROOT":
                verb = token.lemma_
                
                # Find subject (nsubj or nsubjpass)
                subjects = [child for child in token.children 
                           if child.dep_ in ("nsubj", "nsubjpass")]
                
                # Find object (dobj, pobj, or prep -> pobj)
                objects = []
                for child in token.children:
                    if child.dep_ == "dobj":
                        objects.append(child)
                    elif child.dep_ == "prep":
                        # Look for object of preposition
                        for prep_child in child.children:
                            if prep_child.dep_ == "pobj":
                                objects.append(prep_child)
                
                # Create relationships from subjects and objects
                for subj in subjects:
                    for obj in objects:
                        # Get the full entity text (include compounds)
                        subj_text = " ".join([child.text for child in subj.subtree])
                        obj_text = " ".join([child.text for child in obj.subtree])
                        
                        # Check if verb maps to a known relationship type
                        rel_type = VERB_TO_RELATIONSHIP.get(verb, "RELATED_TO")
                        
                        confidence = calculate_confidence(
                            subj_text, obj_text, verb, sent.text
                        )
                        
                        relationships.append(Relationship(
                            source=subj_text,
                            target=obj_text,
                            type=rel_type,
                            reason=f"SVO pattern: '{subj_text}' {verb} '{obj_text}' (sentence: {sent.text[:100]}...)",
                            confidence=confidence,
                            verb=verb
                        ))
    
    return relationships

def infer_relationships(text: str) -> List[Relationship]:
    """
    Infers relationships between entities using enhanced rule-based logic and SVO extraction.
    
    Combines:
    1. Rule-based co-occurrence patterns
    2. SVO (Subject-Verb-Object) dependency parsing
    3. Temporal relationships (DATE entities)
    4. Hierarchical relationships
    """
    cleaned_text = clean_text(text)
    doc = nlp(cleaned_text)
    relationships = []
    
    # Strategy 1: Sentence-level co-occurrence rules
    for sent in doc.sents:
        entities = [(ent.text, ent.label_) for ent in sent.ents]
        
        # Identify entity types
        persons = [e[0] for e in entities if e[1] == "PERSON"]
        orgs = [e[0] for e in entities if e[1] == "ORG"]
        gpes = [e[0] for e in entities if e[1] == "GPE"]
        dates = [e[0] for e in entities if e[1] == "DATE"]
        products = [e[0] for e in entities if e[1] == "PRODUCT"]
        events = [e[0] for e in entities if e[1] == "EVENT"]
        money = [e[0] for e in entities if e[1] == "MONEY"]
        
        sent_lower = sent.text.lower()
        
        # Rule 1: WORKS_AT (PERSON + ORG)
        for person in persons:
            for org in orgs:
                confidence = 0.7
                # Check for role indicators
                if any(indicator in sent_lower for indicator in ["ceo", "founder", "president", "director", "employee"]):
                    confidence = 0.95
                
                relationships.append(Relationship(
                    source=person,
                    target=org,
                    type="WORKS_AT",
                    reason=f"PERSON ({person}) and ORG ({org}) detected in the same sentence with work context.",
                    confidence=confidence
                ))
        
        # Rule 2: LOCATED_IN (ORG + GPE)
        for org in orgs:
            for gpe in gpes:
                confidence = 0.7
                if any(word in sent_lower for word in ["based in", "located in", "headquartered"]):
                    confidence = 0.9
                
                relationships.append(Relationship(
                    source=org,
                    target=gpe,
                    type="LOCATED_IN",
                    reason=f"ORG ({org}) and GPE ({gpe}) detected in the same sentence.",
                    confidence=confidence
                ))
        
        # Rule 3: FOUNDED_IN (ORG + DATE)
        for org in orgs:
            for date in dates:
                if any(word in sent_lower for word in ["founded", "established", "created", "started"]):
                    relationships.append(Relationship(
                        source=org,
                        target=date,
                        type="FOUNDED_IN",
                        reason=f"ORG ({org}) and DATE ({date}) with founding context.",
                        confidence=0.85
                    ))
        
        # Rule 4: OCCURRED_ON (EVENT + DATE)
        for event in events:
            for date in dates:
                relationships.append(Relationship(
                    source=event,
                    target=date,
                    type="OCCURRED_ON",
                    reason=f"EVENT ({event}) and DATE ({date}) detected together.",
                    confidence=0.8
                ))
        
        # Rule 5: PRODUCES (ORG + PRODUCT)
        for org in orgs:
            for product in products:
                confidence = 0.7
                if any(word in sent_lower for word in ["released", "launched", "produced", "developed", "created"]):
                    confidence = 0.9
                
                relationships.append(Relationship(
                    source=org,
                    target=product,
                    type="PRODUCES",
                    reason=f"ORG ({org}) and PRODUCT ({product}) with production context.",
                    confidence=confidence
                ))
        
        # Rule 6: PRICED_AT (PRODUCT + MONEY)
        for product in products:
            for money_val in money:
                if any(word in sent_lower for word in ["cost", "price", "priced", "for"]):
                    relationships.append(Relationship(
                        source=product,
                        target=money_val,
                        type="PRICED_AT",
                        reason=f"PRODUCT ({product}) and MONEY ({money_val}) with pricing context.",
                        confidence=0.85
                    ))
    
    # Strategy 2: SVO-based extraction for semantic relationships
    svo_relationships = extract_svo_relationships(text)
    relationships.extend(svo_relationships)
    
    # Deduplicate relationships
    unique_relationships = []
    seen = set()
    
    for rel in relationships:
        key = (rel.source.lower(), rel.target.lower(), rel.type)
        if key not in seen:
            seen.add(key)
            unique_relationships.append(rel)
    
    return unique_relationships

if __name__ == "__main__":
    sample_text = """
    Apple was founded in 1976 by Steve Jobs. The company is headquartered in Cupertino, California.
    In 2007, Apple released the iPhone for $599. The product sold 1 million units.
    Tim Cook is the CEO of Apple. Microsoft competes with Apple in the tech industry.
    """
    
    print("Inferred Relationships:")
    for r in infer_relationships(sample_text):
        print(f" - {r.source} --[{r.type}]--> {r.target}")
        print(f"   Confidence: {r.confidence:.2f} | Verb: {r.verb} | Reason: {r.reason[:80]}...")
        print()
