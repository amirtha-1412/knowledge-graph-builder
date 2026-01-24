"""
Event extraction module for Knowledge Graph Builder.
Extracts temporal, transaction-based events from text.
"""

import re
from typing import List, Tuple
from app.models import Event, EventType
from app.nlp_engine import extract_dependency_tree

# Event trigger patterns
EVENT_PATTERNS = {
    EventType.ACQUISITION: {
        'triggers': ['acquired', 'bought', 'purchased', 'acquisition of', 'acquires', 'buying'],
        'required_entities': ['ORG'],
        'optional_metadata': ['MONEY', 'DATE']
    },
    EventType.PRODUCT_LAUNCH: {
        'triggers': ['launched', 'released', 'introduced', 'unveiled', 'announced'],
        'required_entities': ['PRODUCT', 'ORG'],
        'optional_metadata': ['DATE', 'MONEY']
    },
    EventType.LEADERSHIP_CHANGE: {
        'triggers': ['appointed', 'named', 'became ceo', 'stepped down', 'resigned', 'hired as'],
        'required_entities': ['PERSON', 'ORG'],
        'optional_metadata': ['DATE']
    },
    EventType.CONFERENCE: {
        'triggers': ['conference', 'summit', 'keynote', 'presentation at', 'speaking at'],
        'required_entities': ['EVENT'],
        'optional_metadata': ['DATE', 'GPE']
    },
    EventType.FUNDING_ROUND: {
        'triggers': ['raised', 'funding round', 'investment', 'series a', 'series b', 'venture capital'],
        'required_entities': ['ORG'],
        'optional_metadata': ['MONEY', 'DATE']
    }
}

def detect_event_type(sentence: str) -> Tuple[EventType, float]:
    """
    Detect event type based on trigger words.
    
    Returns:
        event_type: The detected event type
        confidence: Confidence score (0.0-1.0)
    """
    sentence_lower = sentence.lower()
    
    for event_type, pattern in EVENT_PATTERNS.items():
        for trigger in pattern['triggers']:
            if trigger in sentence_lower:
                # Higher confidence for longer, more specific triggers
                confidence = min(0.9, 0.6 + len(trigger.split()) * 0.1)
                return event_type, confidence
    
    return EventType.OTHER, 0.3

def extract_events(text: str, entities: List, metadata: dict, document_id: str = None) -> List[Event]:
    """
    Extract event entities from text using pattern matching and entity co-occurrence.
    
    Args:
        text: Input text
        entities: List of extracted structural entities
        metadata: Dict of temporal/monetary metadata
        document_id: Document identifier for traceability
    
    Returns:
        List of Event objects
    
    Examples:
        "Apple acquired Beats for $3 billion in 2014"
        -> Acquisition Event:
           - participants: ["Apple", "Beats"]
           - amount: "$3 billion"
           - date: "2014"
    """
    doc = extract_dependency_tree(text)
    events = []
    
    # Create entity lookup by sentence
    entity_by_sentence = {}
    for sent in doc.sents:
        sent_text = sent.text
        sent_entities = [e for e in entities if e.source_sentence == sent_text]
        entity_by_sentence[sent_text] = sent_entities
    
    # Create metadata lookup by sentence
    metadata_by_sentence = {}
    for sent in doc.sents:
        sent_text = sent.text
        metadata_by_sentence[sent_text] = {
            'dates': [m[0] for m in metadata.get('dates', []) if m[1] == sent_text],
            'money': [m[0] for m in metadata.get('money', []) if m[1] == sent_text],
            'locations': [e.text for e in entity_by_sentence.get(sent_text, []) if e.type == 'GPE']
        }
    
    # Process each sentence
    for sent in doc.sents:
        sent_text = sent.text
        sent_entities = entity_by_sentence.get(sent_text, [])
        sent_metadata = metadata_by_sentence.get(sent_text, {})
        
        # Detect event type
        event_type, confidence = detect_event_type(sent_text)
        
        # Skip if no clear event pattern
        if event_type == EventType.OTHER and confidence < 0.5:
            continue
        
        # Check if required entities are present
        pattern = EVENT_PATTERNS.get(event_type, {})
        required_types = pattern.get('required_entities', [])
        
        entity_types_present = set(e.type for e in sent_entities)
        has_required = any(req_type in entity_types_present for req_type in required_types)
        
        if not has_required and event_type != EventType.OTHER:
            continue
        
        # Extract participants
        participants = [e.text for e in sent_entities if e.type in ['PERSON', 'ORG', 'PRODUCT', 'EVENT']]
        
        if not participants:
            continue
        
        # Generate event name
        event_name = generate_event_name(event_type, participants, sent_text)
        
        # Extract metadata
        date = sent_metadata['dates'][0] if sent_metadata['dates'] else None
        amount = sent_metadata['money'][0] if sent_metadata['money'] else None
        location = sent_metadata['locations'][0] if sent_metadata['locations'] else None
        
        # Create event
        event = Event(
            event_type=event_type,
            name=event_name,
            participants=participants,
            date=date,
            location=location,
            amount=amount,
            context=sent_text,
            document_id=document_id,
            confidence=confidence
        )
        
        events.append(event)
    
    # Deduplicate events
    unique_events = []
    seen_events = set()
    
    for event in events:
        event_key = (event.event_type, tuple(sorted(event.participants)))
        if event_key not in seen_events:
            seen_events.add(event_key)
            unique_events.append(event)
    
    return unique_events

def generate_event_name(event_type: EventType, participants: List[str], context: str) -> str:
    """
    Generate a human-readable event name.
    
    Examples:
        ACQUISITION + ["Apple", "Beats"] -> "Apple acquires Beats"
        PRODUCT_LAUNCH + ["Apple", "iPhone"] -> "Apple launches iPhone"
    """
    if event_type == EventType.ACQUISITION:
        if len(participants) >= 2:
            return f"{participants[0]} acquires {participants[1]}"
        return f"{participants[0]} acquisition"
    
    elif event_type == EventType.PRODUCT_LAUNCH:
        orgs = [p for p in participants if 'Inc' in p or 'Corp' in p or len(p.split()) == 1]
        products = [p for p in participants if p not in orgs]
        
        if orgs and products:
            return f"{orgs[0]} launches {products[0]}"
        elif products:
            return f"{products[0]} launch"
        return f"{participants[0]} product launch"
    
    elif event_type == EventType.LEADERSHIP_CHANGE:
        if len(participants) >= 2:
            return f"{participants[0]} joins {participants[1]}"
        return f"{participants[0]} leadership change"
    
    elif event_type == EventType.CONFERENCE:
        return participants[0] if participants else "Conference event"
    
    elif event_type == EventType.FUNDING_ROUND:
        return f"{participants[0]} funding round" if participants else "Funding round"
    
    else:
        return " - ".join(participants[:2]) if participants else "Event"

if __name__ == "__main__":
    # Test event extraction
    from app.nlp_engine import extract_entities
    
    sample_texts = [
        "Apple acquired Beats for $3 billion in 2014.",
        "Google launched Android in 2008.",
        "Tim Cook was named CEO of Apple in 2011.",
        "Microsoft raised $1 billion in Series B funding last year.",
    ]
    
    for text in sample_texts:
        print(f"\nText: {text}")
        entities, metadata = extract_entities(text)
        events = extract_events(text, entities, metadata)
        
        for event in events:
            print(f"  Event: {event.name}")
            print(f"  Type: {event.event_type}")
            print(f"  Participants: {event.participants}")
            print(f"  Date: {event.date}, Amount: {event.amount}")
            print(f"  Confidence: {event.confidence:.2f}")
