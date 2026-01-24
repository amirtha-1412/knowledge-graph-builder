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

# Role-based relationship patterns for specific detection
ROLE_INDICATORS = {
    "FOUNDED": ["founded", "co-founded", "founder of", "founded by"],
    "CEO_OF": ["ceo of", "chief executive of", "ceo", "chief executive officer"],
    "CTO_OF": ["cto of", "chief technology officer"],
    "CFO_OF": ["cfo of", "chief financial officer"],
    "PRESIDENT_OF": ["president of"],
    "DIRECTOR_OF": ["director of"],
    "EMPLOYED_BY": ["works at", "works for", "employee at", "employed by", "working at"],
    "ACQUIRED": ["acquired", "acquired by", "bought", "purchased"],
    "HEADQUARTERED_IN": ["headquartered in", "headquarters in", "based in", "headquartered at"],
}

# Verb mappings for relationship inference
VERB_TO_RELATIONSHIP = {
    # Ownership & Control
    "own": "OWNS",
    "owns": "OWNS",
    "possess": "OWNS",
    "control": "CONTROLS",
    "controls": "CONTROLS",
    
    # Work relationships - More specific
    "found": "FOUNDED",
    "founded": "FOUNDED",
    "co-found": "FOUNDED",
    "employ": "EMPLOYS",
    "employs": "EMPLOYS",
    "hire": "EMPLOYS",
    "hired": "EMPLOYS",
    "work": "EMPLOYED_BY",
    "works": "EMPLOYED_BY",
    
    # Location relationships
    "locate": "LOCATED_IN",
    "located": "LOCATED_IN",
    "base": "HEADQUARTERED_IN",
    "based": "HEADQUARTERED_IN",
    "headquarter": "HEADQUARTERED_IN",
    "headquartered": "HEADQUARTERED_IN",
    
    # Acquisition relationships
    "acquire": "ACQUIRED",
    "acquired": "ACQUIRED",
    "buy": "ACQUIRED",
    "bought": "ACQUIRED",
    "purchase": "ACQUIRED",
    "purchased": "ACQUIRED",
    
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
    
    # Temporal relationships removed - handled as metadata
    "establish": "ESTABLISHED",
    "established": "ESTABLISHED",
    "occur": "OCCURRED",
    "occurred": "OCCURRED",
    "happen": "OCCURRED",
    "happened": "OCCURRED",
    
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

# Minimum confidence threshold for creating relationships
MIN_CONFIDENCE_THRESHOLD = 0.6

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
        "CEO of", "founder of", "president of", "director of", "CTO of", "CFO of",
        "acquired by", "owned by", "produced by", "developed by",
        "part of", "subsidiary of", "division of", "headquartered in",
        "co-founded", "chief executive"
    ]
    
    for indicator in strong_indicators:
        if indicator.lower() in sentence.lower():
            confidence += 0.3
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

def detect_role_relationship(sentence: str, person: str, org: str) -> Tuple[str, float]:
    """
    Detect specific role-based relationships between a person and organization.
    
    Returns:
        relationship_type: Specific role (FOUNDED, CEO_OF, EMPLOYED_BY, etc.)
        confidence: Confidence score
    """
    sent_lower = sentence.lower()
    
    for rel_type, indicators in ROLE_INDICATORS.items():
        for indicator in indicators:
            if indicator in sent_lower:
                # Verify the indicator is near both entities
                person_pos = sent_lower.find(person.lower())
                org_pos = sent_lower.find(org.lower())
                indicator_pos = sent_lower.find(indicator)
                
                if person_pos != -1 and org_pos != -1 and indicator_pos != -1:
                    # Check if indicator is between entities or near them
                    max_distance = max(abs(indicator_pos - person_pos), abs(indicator_pos - org_pos))
                    if max_distance < 80:  # Within 80 characters
                        return rel_type, 0.95
    
    # Fallback to generic EMPLOYED_BY with lower confidence
    return "EMPLOYED_BY", 0.5

def extract_svo_relationships(text: str, metadata: dict = None, document_id: str = None) -> List[Relationship]:
    """
    Extract relationships using Subject-Verb-Object (SVO) parsing.
    Uses SpaCy dependency parsing to find (nsubj, ROOT, dobj/pobj) patterns.
    NO LONGER USES RELATED_TO FALLBACK - only creates relationships when confident.
    """
    doc = extract_dependency_tree(text)
    relationships = []
    
    for sent in doc.sents:
        sent_text = sent.text
        
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
                        rel_type = VERB_TO_RELATIONSHIP.get(verb, None)  # ← NO RELATED_TO FALLBACK
                        
                        # Skip if no known relationship type
                        if rel_type is None:
                            continue
                        
                        confidence = calculate_confidence(
                            subj_text, obj_text, verb, sent_text
                        )
                        
                        # Apply confidence threshold
                        if confidence < MIN_CONFIDENCE_THRESHOLD:
                            continue
                        
                        # Attach metadata if available
                        rel_metadata = {}
                        if metadata:
                            # Find date and money in the same sentence
                            for date_text, date_sent in metadata.get('dates', []):
                                if date_sent == sent_text:
                                    rel_metadata['date'] = date_text
                                    break
                            
                            for money_text, money_sent in metadata.get('money', []):
                                if money_sent == sent_text:
                                    rel_metadata['amount'] = money_text
                                    break
                        
                        relationships.append(Relationship(
                            source=subj_text,
                            target=obj_text,
                            type=rel_type,
                            reason=f"SVO pattern: '{subj_text}' {verb} '{obj_text}'",
                            confidence=confidence,
                            verb=verb,
                            source_sentence=sent_text,
                            document_id=document_id,
                            metadata=rel_metadata if rel_metadata else None
                        ))
    
    return relationships

def infer_relationships(text: str, metadata: dict = None, document_id: str = None) -> List[Relationship]:
    """
    Infers relationships between entities using enhanced rule-based logic and SVO extraction.
    UPDATED: Uses role-based detection, removes RELATED_TO, applies confidence thresholds.
    
    Combines:
    1. Role-based relationship detection (FOUNDED, CEO_OF, EMPLOYED_BY)
    2. SVO (Subject-Verb-Object) dependency parsing
    3. Metadata enrichment (attach DATE, MONEY to relationships, not as nodes)
    4. Confidence-based filtering
    """
    cleaned_text = clean_text(text)
    doc = nlp(cleaned_text)
    relationships = []
    
    # Strategy 1: Sentence-level co-occurrence with role detection
    for sent in doc.sents:
        entities = [(ent.text, ent.label_) for ent in sent.ents]
        
        # Identify STRUCTURAL entity types only (no DATE, MONEY, etc.)
        persons = [e[0] for e in entities if e[1] == "PERSON"]
        orgs = [e[0] for e in entities if e[1] == "ORG"]
        gpes = [e[0] for e in entities if e[1] == "GPE"]
        products = [e[0] for e in entities if e[1] == "PRODUCT"]
        events = [e[0] for e in entities if e[1] == "EVENT"]
        
        sent_text = sent.text
        sent_lower = sent_text.lower()
        
        # Metadata extraction from sentence
        sent_metadata = {}
        if metadata:
            for date_text, date_sent in metadata.get('dates', []):
                if date_sent == sent_text:
                    sent_metadata['date'] = date_text
                    break
            for money_text, money_sent in metadata.get('money', []):
                if money_sent == sent_text:
                    sent_metadata['amount'] = money_text
                    break
        
        # Rule 1: ROLE-BASED RELATIONSHIPS (PERSON + ORG)
        for person in persons:
            for org in orgs:
                # Detect specific role
                rel_type, confidence = detect_role_relationship(sent_text, person, org)
                
                # Apply confidence threshold
                if confidence < MIN_CONFIDENCE_THRESHOLD:
                    continue
                
                relationships.append(Relationship(
                    source=person,
                    target=org,
                    type=rel_type,
                    reason=f"Role-based detection: {person} → {rel_type} → {org}",
                    confidence=confidence,
                    source_sentence=sent_text,
                    document_id=document_id,
                    metadata=sent_metadata if sent_metadata else None
                ))
        
        # Rule 2: HEADQUARTERED_IN (ORG + GPE)
        for org in orgs:
            for gpe in gpes:
                # Check for specific headquarters indicators
                if any(word in sent_lower for word in ["headquartered", "headquarters in", "headquartered in"]):
                    rel_type = "HEADQUARTERED_IN"
                    confidence = 0.95
                elif any(word in sent_lower for word in ["based in", "located in"]):
                    rel_type = "LOCATED_IN"
                    confidence = 0.85
                else:
                    rel_type = "LOCATED_IN"
                    confidence = 0.65
                
                # Apply confidence threshold
                if confidence < MIN_CONFIDENCE_THRESHOLD:
                    continue
                
                relationships.append(Relationship(
                    source=org,
                    target=gpe,
                    type=rel_type,
                    reason=f"Location detection: {org} → {rel_type} → {gpe}",
                    confidence=confidence,
                    source_sentence=sent_text,
                    document_id=document_id
                ))
        
        # REMOVED: FOUNDED_IN, OCCURRED_ON - Dates are now metadata, not nodes
        # These temporal facts are now attached to FOUNDED/ESTABLISHED relationships as metadata
        
        # Rule 3: PRODUCES (ORG + PRODUCT)
        for org in orgs:
            for product in products:
                if any(word in sent_lower for word in ["released", "launched"]):
                    rel_type = "RELEASED"
                    confidence = 0.9
                elif any(word in sent_lower for word in ["produced", "manufactures"]):
                    rel_type = "PRODUCES"
                    confidence = 0.9
                elif any(word in sent_lower for word in ["developed", "created"]):
                    rel_type = "DEVELOPS"
                    confidence = 0.85
                else:
                    rel_type = "PRODUCES"
                    confidence = 0.65
                
                # Apply confidence threshold
                if confidence < MIN_CONFIDENCE_THRESHOLD:
                    continue
                
                relationships.append(Relationship(
                    source=org,
                    target=product,
                    type=rel_type,
                    reason=f"Production detection: {org} → {rel_type} → {product}",
                    confidence=confidence,
                    source_sentence=sent_text,
                    document_id=document_id,
                    metadata=sent_metadata if sent_metadata else None
                ))
        
        # REMOVED: PRICED_AT - Money values are now metadata attached to RELEASED/PRODUCES relationships
    
    # Strategy 2: SVO-based extraction for semantic relationships
    svo_relationships = extract_svo_relationships(text, metadata, document_id)
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
