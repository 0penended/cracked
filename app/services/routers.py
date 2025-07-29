import asyncio
from typing import Dict, Any
from app.models.domain.blockchain import (
    ModelRouter, 
    HeuristicRouter, 
    AlertRouter, 
    UnifiedTransactionEvent, 
    AlertResult
)


# ML Model Routers
class XGBoostModelHL(ModelRouter):
    """XGBoost model router for Hyperliquid transactions."""
    
    async def should_alert(self, event: UnifiedTransactionEvent) -> AlertResult:
        # TODO: Implement actual XGBoost model inference
        # For now, return a simple heuristic
        if event.amount > 1000:  # Large transaction
            return AlertResult(triggered=True, score=0.8, explanation="Large transaction detected")
        return AlertResult(triggered=False, score=0.1)


class XGBoostModelSOL(ModelRouter):
    """XGBoost model router for Solana transactions."""
    
    async def should_alert(self, event: UnifiedTransactionEvent) -> AlertResult:
        # TODO: Implement actual XGBoost model inference
        # For now, return a simple heuristic
        if event.amount > 500:  # Large transaction
            return AlertResult(triggered=True, score=0.7, explanation="Large Solana transaction")
        return AlertResult(triggered=False, score=0.1)


# Heuristic Routers
class VolumeRouter(HeuristicRouter):
    """Router that triggers on high volume transactions."""
    
    def __init__(self, threshold: float = 10000):
        self.threshold = threshold
    
    async def should_alert(self, event: UnifiedTransactionEvent) -> AlertResult:
        if event.amount > self.threshold:
            return AlertResult(
                triggered=True, 
                score=0.9, 
                explanation=f"High volume transaction: {event.amount}"
            )
        return AlertResult(triggered=False, score=0.0)


class BatchedWalletTransactionRouter(HeuristicRouter):
    """Router that tracks batched transactions from the same wallet."""
    
    def __init__(self, batch_threshold: int = 5, time_window: int = 300):
        self.batch_threshold = batch_threshold
        self.time_window = time_window  # seconds
        self.wallet_transactions: Dict[str, list] = {}
    
    async def should_alert(self, event: UnifiedTransactionEvent) -> AlertResult:
        current_time = event.timestamp // 1000  # Convert to seconds
        
        # Initialize wallet tracking if not exists
        if event.wallet not in self.wallet_transactions:
            self.wallet_transactions[event.wallet] = []
        
        # Add current transaction
        self.wallet_transactions[event.wallet].append(current_time)
        
        # Remove old transactions outside time window
        self.wallet_transactions[event.wallet] = [
            t for t in self.wallet_transactions[event.wallet] 
            if current_time - t < self.time_window
        ]
        
        # Check if threshold exceeded
        if len(self.wallet_transactions[event.wallet]) >= self.batch_threshold:
            return AlertResult(
                triggered=True,
                score=0.8,
                explanation=f"Batched transactions: {len(self.wallet_transactions[event.wallet])} in {self.time_window}s"
            )
        
        return AlertResult(triggered=False, score=0.0)


class SizeRouter(HeuristicRouter):
    """Router that triggers on unusual transaction sizes."""
    
    def __init__(self, size_threshold: float = 100):
        self.size_threshold = size_threshold
    
    async def should_alert(self, event: UnifiedTransactionEvent) -> AlertResult:
        if event.amount > self.size_threshold:
            return AlertResult(
                triggered=True,
                score=0.6,
                explanation=f"Unusual transaction size: {event.amount}"
            )
        return AlertResult(triggered=False, score=0.0)


# Alert Routers
class TelegramAlertRouter(AlertRouter):
    """Router that sends alerts to Telegram."""
    
    def __init__(self, config: Dict[str, Any]):
        self.bot_token = config.get("bot_token")
        self.chat_id = config.get("chat_id")
        self.chain_name = config.get("chain_name", "Unknown")
    
    async def send(self, event: UnifiedTransactionEvent, results: list[AlertResult]):
        """Send alert to Telegram."""
        if not self.bot_token or not self.chat_id:
            print("Telegram configuration missing")
            return
        
        # Build message
        message = self._build_message(event, results)
        
        # Send to Telegram
        await self._send_telegram_message(message)
    
    def _build_message(self, event: UnifiedTransactionEvent, results: list[AlertResult]) -> str:
        """Build alert message for Telegram."""
        message = f"🚨 {self.chain_name.upper()} ALERT 🚨\n\n"
        message += f"Wallet: `{event.wallet}`\n"
        message += f"Transaction: `{event.tx_hash}`\n"
        message += f"Action: {event.action}\n"
        message += f"Amount: {event.amount}\n"
        if event.symbol:
            message += f"Symbol: {event.symbol}\n"
        if event.price:
            message += f"Price: {event.price}\n"
        
        message += f"\nTriggers:\n"
        for i, result in enumerate(results, 1):
            message += f"{i}. Score: {result.score:.2f} - {result.explanation}\n"
        
        return message
    
    async def _send_telegram_message(self, message: str):
        """Send message to Telegram."""
        try:
            import aiohttp
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status != 200:
                        print(f"Failed to send Telegram message: {response.status}")
                        
        except Exception as e:
            print(f"Error sending Telegram message: {e}")


# Database Writers
class PostgresWriter:
    """PostgreSQL writer for blockchain events."""
    
    def __init__(self, db_pool=None):
        self.db_pool = db_pool
    
    async def insert(self, event: UnifiedTransactionEvent):
        """Insert event into PostgreSQL database."""
        try:
            # TODO: Implement actual database insertion
            # This would use your existing database infrastructure
            print(f"[DB] Inserting {event.chain} transaction: {event.tx_hash}")
            
            # Example using your existing transaction service
            # from app.services.transactions import TransactionsService
            # from app.models.schemas.transactions import TransactionInCreate
            # 
            # transaction_in = TransactionInCreate(
            #     wallet_address=event.wallet,
            #     type=event.action,
            #     timestamp=event.timestamp,
            #     # ... map other fields
            # )
            # 
            # await self.transaction_service.create_transaction(transaction_in=transaction_in)
            
        except Exception as e:
            print(f"Error inserting transaction to database: {e}") 