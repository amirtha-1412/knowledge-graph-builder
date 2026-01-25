// Clean up old DATE/MONEY nodes that violate semantic validation
// Run this in Neo4j Browser: http://localhost:7474

// Step 1: Delete all DATE, MONEY, PERCENT nodes (these should be metadata now)
MATCH (n:Entity)
WHERE n.type IN ['DATE', 'MONEY', 'PERCENT', 'CARDINAL', 'ORDINAL']
DETACH DELETE n;

// Step 2: Verify only valid entity types remain
MATCH (n:Entity)
RETURN DISTINCT n.type, count(*) as count
ORDER BY count DESC;

// Expected types: PERSON, ORG (COMPANY), GPE (LOCATION), PRODUCT
// Should NOT see: DATE, MONEY, PERCENT, etc.
