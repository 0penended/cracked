-- name: create_strategy
INSERT INTO strategies (type, description, parameters, is_active, created_at) 
VALUES (:type, :description, :parameters, :is_active, :created_at) 
RETURNING *;

-- name: get_strategy_by_type
SELECT id, type, description, parameters, is_active, created_at
FROM strategies 
WHERE type = :type AND is_active = true
LIMIT 1;

-- name: get_all_active_strategies
SELECT id, type, description, parameters, is_active, created_at
FROM strategies 
WHERE is_active = true
ORDER BY type, description;

-- name: create_transaction_strategy
INSERT INTO transaction_strategies (transaction_id, strategy_id, confidence, explanation, metadata, created_at) 
VALUES (:transaction_id, :strategy_id, :confidence, :explanation, :metadata, :created_at) 
RETURNING *;

-- name: get_transaction_strategies
SELECT ts.id, ts.transaction_id, ts.strategy_id, ts.confidence, ts.explanation, ts.metadata, ts.created_at, s.description as strategy_description, s.type
FROM transaction_strategies ts
JOIN strategies s ON ts.strategy_id = s.id
WHERE ts.transaction_id = :transaction_id
ORDER BY ts.created_at DESC;

-- name: get_strategy_statistics
SELECT s.type, s.description as strategy_description, COUNT(*) as total_matches, AVG(ts.confidence) as avg_confidence, MIN(ts.confidence) as min_confidence, MAX(ts.confidence) as max_confidence, COUNT(DISTINCT ts.transaction_id) as unique_transactions
FROM transaction_strategies ts
JOIN strategies s ON ts.strategy_id = s.id
JOIN transactions t ON ts.transaction_id = t.id
WHERE (:type IS NULL OR s.type = :type) AND (:start_timestamp IS NULL OR t.timestamp >= :start_timestamp) AND (:end_timestamp IS NULL OR t.timestamp <= :end_timestamp) AND s.is_active = true
GROUP BY s.type, s.description
ORDER BY total_matches DESC; 