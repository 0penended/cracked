import pytest
from httpx import AsyncClient

from app.models.domain.transactions import Transaction


@pytest.mark.asyncio
async def test_create_transaction(async_client: AsyncClient) -> None:
    transaction_data = {
        "transaction": {
            "wallet_address": "0x1234567890abcdef",
            "type": "BUY",
            "received_token_id": "0xabcdef1234567890",
            "received_token_marketcap": 1000000.0,
            "received_token_price": 1.5,
            "received_token_quantity": 100.0,
            "received_token_symbol": "TEST",
            "received_token_volume_h24": 50000.0,
            "received_token_price_change_h24": 5.0,
            "received_token_liquidity": 100000.0,
            "received_token_created_at": 1640995200,
            "spent_token_id": "0xabcdef1234567890",
            "spent_token_marketcap": 2000000.0,
            "spent_token_price": 2.0,
            "spent_token_quantity": 50.0,
            "spent_token_symbol": "USDC",
            "spent_token_volume_h24": 100000.0,
            "spent_token_price_change_h24": -2.0,
            "spent_token_liquidity": 200000.0,
            "spent_token_created_at": 1640995200,
        }
    }

    response = await async_client.post("/api/transactions", json=transaction_data)
    assert response.status_code == 200

    data = response.json()
    assert "transaction" in data
    transaction = data["transaction"]
    assert transaction["wallet_address"] == "0x1234567890abcdef"
    assert transaction["type"] == "BUY"
    assert transaction["received_token_symbol"] == "TEST"


@pytest.mark.asyncio
async def test_get_all_transactions(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/transactions")
    assert response.status_code == 200

    data = response.json()
    assert "transactions" in data
    assert "transactions_count" in data
    assert isinstance(data["transactions"], list)


@pytest.mark.asyncio
async def test_get_transaction_by_id(async_client: AsyncClient) -> None:
    # First create a transaction
    transaction_data = {
        "transaction": {
            "wallet_address": "0x1234567890abcdef",
            "type": "SELL",
            "spent_token_id": "0xabcdef1234567890",
            "spent_token_symbol": "TOKEN",
            "spent_token_quantity": 50.0,
            "spent_token_price": 2.0,
            "spent_token_marketcap": 2000000.0,
        }
    }

    create_response = await async_client.post(
        "/api/transactions", json=transaction_data
    )
    assert create_response.status_code == 200

    created_transaction = create_response.json()["transaction"]
    transaction_id = created_transaction["id"]

    # Then get it by ID
    response = await async_client.get(f"/api/transactions/{transaction_id}")
    assert response.status_code == 200

    data = response.json()
    assert "transaction" in data
    transaction = data["transaction"]
    assert transaction["id"] == transaction_id
    assert transaction["type"] == "SELL"


@pytest.mark.asyncio
async def test_get_transactions_by_wallet_address(async_client: AsyncClient) -> None:
    wallet_address = "0x9876543210fedcba"

    # Create a transaction for this wallet
    transaction_data = {
        "transaction": {
            "wallet_address": wallet_address,
            "type": "SWAP",
            "received_token_id": "0x1111111111111111",
            "received_token_symbol": "TOKEN1",
            "received_token_quantity": 10.0,
            "spent_token_id": "0x2222222222222222",
            "spent_token_symbol": "TOKEN2",
            "spent_token_quantity": 20.0,
        }
    }

    await async_client.post("/api/transactions", json=transaction_data)

    # Get transactions for this wallet
    response = await async_client.get(f"/api/transactions/wallet/{wallet_address}")
    assert response.status_code == 200

    data = response.json()
    assert "transactions" in data
    assert "transactions_count" in data
    assert data["transactions_count"] >= 1

    # Check that the transaction belongs to the correct wallet
    transactions = data["transactions"]
    assert any(t["wallet_address"] == wallet_address for t in transactions)


@pytest.mark.asyncio
async def test_get_transactions_by_type(async_client: AsyncClient) -> None:
    # Create a BUY transaction
    transaction_data = {
        "transaction": {
            "wallet_address": "0x5555555555555555",
            "type": "BUY",
            "received_token_symbol": "BUYTOKEN",
        }
    }

    await async_client.post("/api/transactions", json=transaction_data)

    # Get BUY transactions
    response = await async_client.get("/api/transactions/type/BUY")
    assert response.status_code == 200

    data = response.json()
    assert "transactions" in data
    assert "transactions_count" in data
    assert data["transactions_count"] >= 1

    # Check that all transactions are of type BUY
    transactions = data["transactions"]
    assert all(t["type"] == "BUY" for t in transactions)


@pytest.mark.asyncio
async def test_invalid_transaction_type(async_client: AsyncClient) -> None:
    transaction_data = {
        "transaction": {
            "wallet_address": "0x1234567890abcdef",
            "type": "INVALID_TYPE",  # Invalid type
        }
    }

    response = await async_client.post("/api/transactions", json=transaction_data)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_transaction(async_client: AsyncClient) -> None:
    # First create a transaction
    transaction_data = {
        "transaction": {
            "wallet_address": "0x1234567890abcdef",
            "type": "BUY",
            "received_token_symbol": "OLDTOKEN",
        }
    }

    create_response = await async_client.post(
        "/api/transactions", json=transaction_data
    )
    assert create_response.status_code == 200

    created_transaction = create_response.json()["transaction"]
    transaction_id = created_transaction["id"]

    # Update the transaction
    update_data = {
        "transaction": {
            "received_token_symbol": "NEWTOKEN",
        }
    }

    response = await async_client.put(
        f"/api/transactions/{transaction_id}", json=update_data
    )
    assert response.status_code == 200

    data = response.json()
    assert "transaction" in data
    transaction = data["transaction"]
    assert transaction["received_token_symbol"] == "NEWTOKEN"
    assert transaction["type"] == "BUY"  # Should remain unchanged


@pytest.mark.asyncio
async def test_delete_transaction(async_client: AsyncClient) -> None:
    # First create a transaction
    transaction_data = {
        "transaction": {
            "wallet_address": "0x1234567890abcdef",
            "type": "BUY",
        }
    }

    create_response = await async_client.post(
        "/api/transactions", json=transaction_data
    )
    assert create_response.status_code == 200

    created_transaction = create_response.json()["transaction"]
    transaction_id = created_transaction["id"]

    # Delete the transaction
    response = await async_client.delete(f"/api/transactions/{transaction_id}")
    assert response.status_code == 200

    # Try to get the deleted transaction
    get_response = await async_client.get(f"/api/transactions/{transaction_id}")
    assert get_response.status_code == 404
