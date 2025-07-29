import asyncio
import time
from typing import Set

from solders.rpc.responses import LogsNotification
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient as HttpClient
from solana.rpc.websocket_api import (
    connect as ws_connect,
    RpcTransactionLogsFilterMentions,
)

from app.models.domain.blockchain import ChainListener, UnifiedTransactionEvent
from app.services.pipeline import CoreTransactionPipeline

import httpx

print(httpx.__version__)


class SolanaListener(ChainListener):
    def __init__(self, pipeline: CoreTransactionPipeline, rpc_url: str, ws_url: str):
        self.pipeline = pipeline
        self.http_client = HttpClient(rpc_url)
        self.ws_url = ws_url
        self.addresses: Set[str] = set()
        self.recent_signatures: Set[str] = set()
        self.conn = None

    async def subscribe_wallets(self, addresses: list[str]):
        for addr in addresses:
            self.addresses.add(addr)

    async def run(self):
        self.conn = await ws_connect(self.ws_url)
        print("[Solana] Connected to WebSocket.")

        # Subscribe to logs for each address
        for address in self.addresses:
            pk = Pubkey.from_string(address)
            await self.conn.logs_subscribe(
                filter_=RpcTransactionLogsFilterMentions(pubkey=pk),
                commitment="confirmed",
            )
            print(f"[Solana] Subscribed to logs for wallet {address}")

        try:
            async for msgs in self.conn:
                print("!!!msg!!!", msgs)
                if not isinstance(msgs, list):
                    msgs = [msgs]
                for msg in msgs:
                    if isinstance(msg, LogsNotification) and self._is_relevant_log(
                        msg.result.value.logs
                    ):
                        notification_value = msg.result.value
                        signature = notification_value.signature
                        if signature in self.recent_signatures:
                            continue
                        self.recent_signatures.add(signature)
                        if len(self.recent_signatures) > 10000:
                            self.recent_signatures.pop()
                        asyncio.create_task(
                            self._handle_transaction(
                                signature,
                                "EgaYt5xZK4qeWphbKD42oxzbeArYkWY9WCxrQBk9F6r5",
                            )
                        )

        except Exception as e:
            print(f"[Solana] WebSocket error: {e}")
        finally:
            if self.conn:
                await self.conn.close()

    def _is_relevant_log(self, logs: list[str]) -> bool:
        relevant_keywords = [
            "instruction: transfer",
            "instruction: swap",
            "swapevent",
            "dex::",
            "commission_amount",
            "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
        ]
        return any(
            keyword.lower() in log.lower()
            for log in logs
            for keyword in relevant_keywords
        )

    async def _handle_transaction(self, signature: str, wallet: str):
        try:
            tx = None
            for _ in range(3):
                tx = await self.http_client.get_transaction(
                    signature,
                    encoding="jsonParsed",
                    commitment="confirmed",
                    max_supported_transaction_version=0,
                )
                print("!!!tx!!!", tx)
                if tx and tx.get("result"):
                    break
                await asyncio.sleep(1)

            if not tx or not tx.get("result"):
                print(f"[Solana] Transaction not found: {signature}")
                return

            result = tx["result"]
            parsed_instruction = self._parse_transaction(result)
            if not parsed_instruction:
                return

            event = UnifiedTransactionEvent(
                chain="solana",
                wallet=str(wallet),
                tx_hash=signature,
                timestamp=int(time.time() * 1000),
                symbol=parsed_instruction["symbol"],
                action=parsed_instruction["action"],
                amount=parsed_instruction["amount"],
                metadata=result,
            )

            # await self.pipeline.handle_event(event)

        except Exception as e:
            print(f"[Solana] Error handling transaction {signature}: {e}")

    def _parse_transaction(self, tx_result) -> dict:
        try:
            meta = tx_result.get("meta", {})
            log_messages = meta.get("logMessages", [])
            symbol = "SOL"
            action = "TRANSFER"
            amount = 1.0
            return {
                "symbol": symbol,
                "action": action,
                "amount": amount,
            }
        except Exception as e:
            print(f"[Solana] Error parsing transaction: {e}")
            return None
