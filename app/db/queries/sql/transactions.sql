-- name: create-new-transaction<!
INSERT INTO transactions (
    wallet_address,
    type,
    timestamp,
    received_token_ca,
    received_token_marketcap,
    received_token_price,
    received_token_quantity,
    received_token_symbol,
    spent_token_ca,
    spent_token_marketcap,
    spent_token_price,
    spent_token_quantity,
    spent_token_symbol
)
VALUES (
    :wallet_address,
    :type,
    :timestamp,
    :received_token_ca,
    :received_token_marketcap,
    :received_token_price,
    :received_token_quantity,
    :received_token_symbol,
    :spent_token_ca,
    :spent_token_marketcap,
    :spent_token_price,
    :spent_token_quantity,
    :spent_token_symbol
)
RETURNING id;