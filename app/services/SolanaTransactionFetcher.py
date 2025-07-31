import asyncio
import time
from typing import Optional, Dict, Any

from solders.rpc.responses import GetTransactionResp
from solana.rpc.async_api import AsyncClient as HttpClient
from app.clients.DexScreenerClient import DexScreenerClient
from app.models.domain.blockchain import UnifiedTransactionEvent, Action


class SolanaTransactionFetcher:
    """Handles fetching and parsing Solana transactions."""

    # Token contract addresses
    SOL_CA = "So11111111111111111111111111111111111111112"
    USDC_CA = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

    def __init__(self, rpc_url: str, dex_screener_client: DexScreenerClient):
        self.http_client = HttpClient(rpc_url)
        self.dex_screener_client = dex_screener_client

    async def fetch_and_parse_transaction(
        self, signature: str
    ) -> Optional[UnifiedTransactionEvent]:
        """Fetch a transaction and parse its token deltas."""
        try:
            tx = None
            for _ in range(3):
                tx = await self.http_client.get_transaction(
                    signature,
                    encoding="jsonParsed",
                    commitment="confirmed",
                    max_supported_transaction_version=0,
                )
                if tx.value:
                    break
                await asyncio.sleep(1)

            if not tx or not tx.value:
                print(f"[Solana] Transaction not found: {signature}")
                return None

            parsed_data = self._parse_token_deltas(tx)
            if not parsed_data:
                return None

            token_deltas = parsed_data["token_deltas"]
            wallet_address = parsed_data["wallet_address"]

            return await self._create_unified_event(
                token_deltas, signature, wallet_address
            )

        except Exception as e:
            print(f"[Solana] Error fetching transaction {signature}: {e}")
            return None

    async def _create_unified_event(
        self, token_deltas: Dict[str, Any], signature: str, wallet_address: str
    ) -> UnifiedTransactionEvent:
        """Create a UnifiedTransactionEvent from parsed token deltas."""
        received_token = token_deltas.get("received")
        spent_token = token_deltas.get("spent")
        transaction_type = token_deltas.get("transaction_type", "SWAP")

        # Determine action based on transaction type
        if transaction_type == "BUY":
            action = Action.BUY
        elif transaction_type == "SELL":
            action = Action.SELL
        else:
            action = Action.SWAP

        # Collect all token addresses to fetch
        token_addresses = []
        if received_token:
            token_addresses.append(received_token["mint"])
        if spent_token:
            token_addresses.append(spent_token["mint"])

        # Fetch metadata for all tokens in a single call
        all_metadata = {}
        if token_addresses:
            try:
                metadata_list = (
                    await self.dex_screener_client.fetch_dex_token_data_multi(
                        token_addresses
                    )
                )
                for metadata in metadata_list:
                    if metadata and "pairs" in metadata and metadata["pairs"]:
                        # Use the first pair's baseToken address as the key
                        base_token_address = (
                            metadata["pairs"][0].get("baseToken", {}).get("address")
                        )
                        if base_token_address:
                            all_metadata[base_token_address] = metadata
            except Exception as e:
                print(f"[Solana] Error fetching multi-token metadata: {e}")

        # Get metadata for received and spent tokens
        received_pair_data = None
        spent_pair_data = None
        received_symbol = "UNKNOWN"
        spent_symbol = "UNKNOWN"

        if received_token and spent_token:
            # Get received token metadata
            received_token_address = received_token["mint"]
            if received_token_address in all_metadata:
                received_metadata = all_metadata[received_token_address]
                if received_metadata.get("pairs"):
                    received_pair_data = received_metadata["pairs"][
                        0
                    ]  # Most liquid pair
                    received_symbol = received_pair_data.get("baseToken", {}).get(
                        "symbol", "UNKNOWN"
                    )
                else:
                    print(
                        f"No pairs found for received token: {received_token_address}"
                    )
            else:
                print(f"No metadata found for received token: {received_token_address}")

            # Get spent token metadata
            spent_token_address = spent_token["mint"]
            if spent_token_address in all_metadata:
                spent_metadata = all_metadata[spent_token_address]
                if spent_metadata.get("pairs"):
                    spent_pair_data = spent_metadata["pairs"][0]  # Most liquid pair
                    spent_symbol = (
                        spent_metadata["pairs"][0]
                        .get("baseToken", {})
                        .get("symbol", "UNKNOWN")
                    )
                else:
                    print(f"No pairs found for spent token: {spent_token_address}")
            else:
                print(f"No metadata found for spent token: {spent_token_address}")

        # Extract final values
        received_price = self._extract_price(
            received_pair_data, received_token["mint"] if received_token else None
        )
        received_volume = self._extract_volume_24h(received_pair_data)
        received_liquidity = self._extract_liquidity(received_pair_data)

        spent_price = self._extract_price(
            spent_pair_data, spent_token["mint"] if spent_token else None
        )
        spent_volume = self._extract_volume_24h(spent_pair_data)
        spent_liquidity = self._extract_liquidity(spent_pair_data)

        # Create the unified event
        event = UnifiedTransactionEvent(
            chain="solana",
            wallet_address=wallet_address,
            txn_hash=signature,
            timestamp=int(time.time() * 1000),
            action=action,
            recieved_token_id=received_token["mint"] if received_token else None,
            recieved_token_symbol=received_symbol,
            recieved_token_quantity=received_token["amount"] if received_token else 0.0,
            recieved_token_price=received_price,
            recieved_token_volume_h24=received_volume,
            recieved_token_price_change_h24=self._extract_price_change_24h(
                received_pair_data
            ),
            recieved_token_liquidity=received_liquidity,
            recieved_token_created_at=(
                received_pair_data.get("pairCreatedAt", 0) if received_pair_data else 0
            ),
            spent_token_id=spent_token["mint"] if spent_token else None,
            spent_token_symbol=spent_symbol,
            spent_token_amount=spent_token["amount"] if spent_token else 0.0,
            spent_token_price=spent_price,
            spent_token_volume_h24=spent_volume,
            spent_token_price_change_h24=self._extract_price_change_24h(
                spent_pair_data
            ),
            spent_token_liquidity=spent_liquidity,
            spent_token_created_at=(
                spent_pair_data.get("pairCreatedAt", 0) if spent_pair_data else 0
            ),
        )

        return event

    def _extract_price(
        self, pair_data: Optional[Dict[str, Any]], token_mint: Optional[str]
    ) -> float:
        """Extract price from pair data."""
        if not pair_data or not token_mint:
            return 0.0

        base_token = pair_data.get("baseToken", {})
        quote_token = pair_data.get("quoteToken", {})

        if base_token.get("address") == token_mint:
            return float(pair_data.get("priceUsd", 0))
        elif quote_token.get("address") == token_mint:
            # For quote token, we need to calculate inverse price
            price_usd = float(pair_data.get("priceUsd", 0))
            return 1.0 / price_usd if price_usd > 0 else 0.0

        return 0.0

    def _extract_volume_24h(self, pair_data: Optional[Dict[str, Any]]) -> float:
        """Extract 24h volume from pair data."""
        if not pair_data:
            return 0.0
        return float(pair_data.get("volume", {}).get("h24", 0))

    def _extract_price_change_24h(self, pair_data: Optional[Dict[str, Any]]) -> float:
        """Extract 24h price change from pair data."""
        if not pair_data:
            return 0.0
        return float(pair_data.get("priceChange", {}).get("h24", 0))

    def _extract_liquidity(self, pair_data: Optional[Dict[str, Any]]) -> float:
        """Extract liquidity from pair data."""
        if not pair_data:
            return 0.0
        return float(pair_data.get("liquidity", {}).get("usd", 0))

    def _is_usdc(self, token_id: str) -> bool:
        """Check if token is USDC."""
        return token_id == self.USDC_CA

    def _is_sol(self, token_id: str) -> bool:
        """Check if token is SOL."""
        return token_id == self.SOL_CA

    def _is_stable_coin(self, token_id: str) -> bool:
        """Check if token is a stable coin (USDC or SOL)."""
        return self._is_usdc(token_id) or self._is_sol(token_id)

    def _get_transaction_type(self, received_token_id: str, spent_token_id: str) -> str:
        """Determine transaction type based on received and spent tokens."""

        # Special case: USDC ↔ SOL transactions
        if self._is_usdc(received_token_id) and self._is_sol(spent_token_id):
            return "SELL"  # Receiving USDC for SOL = selling SOL for USDC
        if self._is_sol(received_token_id) and self._is_usdc(spent_token_id):
            return "BUY"  # Receiving SOL for USDC = buying SOL with USDC

        # If received stable coin (USDC or SOL) and spent non-stable, it's a SELL
        if self._is_stable_coin(received_token_id) and not self._is_stable_coin(
            spent_token_id
        ):
            return "SELL"

        # If spent stable coin (USDC or SOL) and received non-stable, it's a BUY
        if not self._is_stable_coin(received_token_id) and self._is_stable_coin(
            spent_token_id
        ):
            return "BUY"

        # Otherwise it's a SWAP (SPL for SPL)
        return "SWAP"

    def _parse_token_deltas(self, raw: GetTransactionResp) -> Optional[Dict[str, Any]]:
        """Parse token deltas from a Solana transaction response."""
        if not raw.value:
            return None

        txn = raw.value.transaction.transaction
        meta = raw.value.transaction.meta

        # Get wallet address (fee payer)
        wallet_address = str(txn.message.account_keys[0].pubkey)

        # Guard: meta must exist and include SPL token balances
        if not meta or not meta.pre_token_balances or not meta.post_token_balances:
            return None

        def to_spl_token_map(balances):
            mapping = {}
            for b in balances:
                owner = str(b.owner) if b.owner is not None else None
                mint = str(b.mint)
                amt = b.ui_token_amount.ui_amount
                if owner == wallet_address and amt is not None:
                    mapping[mint] = float(amt)
            return mapping

        # Get SPL token deltas
        pre_spl = to_spl_token_map(meta.pre_token_balances)
        post_spl = to_spl_token_map(meta.post_token_balances)

        spl_deltas = {
            mint: post_spl.get(mint, 0.0) - pre_spl.get(mint, 0.0)
            for mint in set(pre_spl) | set(post_spl)
        }

        spl_received = [(mint, amt) for mint, amt in spl_deltas.items() if amt > 0]
        spl_spent = [(mint, amt) for mint, amt in spl_deltas.items() if amt < 0]

        # Get SOL delta using pre/post balances by index
        sol_delta = None
        if meta.pre_balances and meta.post_balances:
            for i, key in enumerate(txn.message.account_keys):
                if str(key.pubkey) == wallet_address:
                    lamport_delta = meta.post_balances[i] - meta.pre_balances[i]
                    sol_delta = lamport_delta / 1e9  # Convert to SOL
                    break

        # Format output - handle both SPL and SOL for received and spent
        received_token = None
        spent_token = None

        # Helper function to prioritize tokens (USDC first, then SOL, then others)
        def prioritize_tokens(token_list):
            if not token_list:
                return None

            # First, look for USDC
            for mint, amount in token_list:
                if mint == self.USDC_CA:
                    return mint, amount

            # Then look for SOL
            for mint, amount in token_list:
                if mint == self.SOL_CA:
                    return mint, amount

            # Otherwise return the first token
            return token_list[0]

        # Check if SPL token was received
        if spl_received:
            prioritized_received = prioritize_tokens(spl_received)
            if prioritized_received:
                received_token = {
                    "mint": prioritized_received[0],
                    "amount": round(prioritized_received[1], 6),
                }
        # Check if SOL was received (positive delta)
        elif sol_delta is not None and sol_delta > 0:
            received_token = {"mint": self.SOL_CA, "amount": round(sol_delta, 6)}

        # Check if SPL token was spent
        if spl_spent:
            prioritized_spent = prioritize_tokens(spl_spent)
            if prioritized_spent:
                spent_token = {
                    "mint": prioritized_spent[0],
                    "amount": round(abs(prioritized_spent[1]), 6),
                }
        # Check if SOL was spent (negative delta)
        elif sol_delta is not None and sol_delta < 0:
            spent_token = {
                "mint": self.SOL_CA,
                "amount": round(abs(sol_delta), 6),
            }

        # Determine transaction type
        transaction_type = None
        if received_token and spent_token:
            transaction_type = self._get_transaction_type(
                received_token["mint"], spent_token["mint"]
            )

        token_deltas = {
            "received": received_token,
            "spent": spent_token,
            "transaction_type": transaction_type,
        }

        return {
            "token_deltas": token_deltas,
            "wallet_address": wallet_address,
        }
