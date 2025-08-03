import asyncio
from typing import Dict, Any
import asyncpg

from app.core.settings.app import AppSettings
from app.services.pipeline.core import CoreTransactionPipeline
from app.services.listeners.solana import SolanaListener
from app.services.fetchers.solana import SolanaTransactionFetcher
from app.services.listeners.hyperliquid import HyperliquidListener
from app.services.fetchers.hyperliquid import HyperliquidTransactionFetcher
from app.clients.CoinMarketCapClient import CoinMarketCapClient
from app.clients.DexScreenerClient import DexScreenerClient
from app.clients.TelegramClient import TelegramClient
from app.models.domain.blockchain import UnifiedTransactionEvent
from app.services.routers import (
    XGBoostModelHL,
    XGBoostModelSOL,
    VolumeRouter,
    BatchedWalletTransactionRouter,
    SizeRouter,
    TelegramAlertRouter,
)
from app.db.repositories.transactions import TransactionsRepository
from dotenv import load_dotenv

load_dotenv(override=True)

settings = AppSettings()


async def main():
    """Main blockchain monitoring application."""

    # Create database connection
    db_conn = await asyncpg.connect(settings.database_url)

    # Create database writer with connection
    db_writer = TransactionsRepository(db_conn)

    # Create clients
    coinmarketcap_client = CoinMarketCapClient(
        api_key=settings.coinmarketcap_api_key,
        base_url=settings.coinmarketcap_base_url,
    )

    telegram_client = TelegramClient(settings.telegram_bot_token)

    # Create Hyperliquid pipeline
    pipeline_hyperliquid = CoreTransactionPipeline(
        db_writer=db_writer,
        model_routers=[],
        heuristic_routers=[
            VolumeRouter(threshold=1000000),
            BatchedWalletTransactionRouter(batch_threshold=5, time_window=1800),
            SizeRouter(size_threshold=10000),
        ],
        alert_router=TelegramAlertRouter(
            telegram_client=telegram_client,
            chat_id=settings.telegram_chat_id,
            chain_name="Hyperliquid",
        ),
    )

    hyperliquid_transaction_fetcher = HyperliquidTransactionFetcher(
        coinmarketcap_client=coinmarketcap_client
    )

    hyperliquid_listener = HyperliquidListener(
        pipeline=pipeline_hyperliquid,
        transaction_fetcher=hyperliquid_transaction_fetcher,
    )
    await hyperliquid_listener.subscribe_wallets(
        ["0x576A41Ba10520568811E1465CABb52aBfE6beAdc"]
    )

    # Create Solana pipeline
    # pipeline_solana = CoreTransactionPipeline(
    #     db_writer=db_writer,
    #     model_routers=[XGBoostModelSOL()],
    #     heuristic_routers=[
    #         BatchedWalletTransactionRouter(batch_threshold=3, time_window=300),
    #         SizeRouter(size_threshold=50),
    #     ],
    #     alert_router=TelegramAlertRouter(
    #         telegram_client=telegram_client,
    #         chat_id=settings.telegram_chat_id,
    #         chain_name="Solana"
    #     ),
    # )

    # Create DexScreener client
    # dex_screener_client = DexScreenerClient()
    # # Create Solana transaction fetcher
    # solana_transaction_fetcher = SolanaTransactionFetcher(
    #     settings.solana_rpc_url, dex_screener_client
    # )

    # # Create Solana listener
    # solana_listener = SolanaListener(
    #     ws_url=settings.solana_ws_url,
    #     transaction_fetcher=solana_transaction_fetcher,
    #     pipeline_handler=pipeline_solana,
    # )
    # # hyperliquid_listener = HyperliquidListener(pipeline_hyperliquid)

    # # Subscribe to wallets
    # await solana_listener.subscribe_wallets(
    #     ["EgaYt5xZK4qeWphbKD42oxzbeArYkWY9WCxrQBk9F6r5"]
    # )

    print("🚀 Starting blockchain monitoring...")
    print("📡 Monitoring Solana and Hyperliquid chains")
    print("🔔 Alerts will be sent to configured Telegram channels")

    # Run all listeners concurrently
    try:
        await asyncio.gather(
            # solana_listener.run(),
            hyperliquid_listener.run()
        )
    except KeyboardInterrupt:
        print("\n🛑 Shutting down blockchain monitoring...")
    except Exception as e:
        print(f"❌ Error in main loop: {e}")
    finally:
        # Close database connection
        await db_conn.close()


if __name__ == "__main__":
    asyncio.run(main())
