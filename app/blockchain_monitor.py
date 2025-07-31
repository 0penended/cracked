import asyncio
from typing import Dict, Any

from app.core.settings.app import AppSettings
from app.services.pipeline import CoreTransactionPipeline
from app.services.SolanaListener import SolanaListener
from app.services.SolanaTransactionFetcher import SolanaTransactionFetcher
from app.services.HyperliquidListener import HyperliquidListener
from app.services.HyperliquidTransactionFetcher import HyperliquidTransactionFetcher
from app.clients.CoinMarketCapClient import CoinMarketCapClient
from app.clients.DexScreenerClient import DexScreenerClient
from app.models.domain.blockchain import UnifiedTransactionEvent
from app.services.routers import (
    XGBoostModelHL,
    XGBoostModelSOL,
    VolumeRouter,
    BatchedWalletTransactionRouter,
    SizeRouter,
    TelegramAlertRouter,
    PostgresWriter,
)
from dotenv import load_dotenv

load_dotenv(override=True)

settings = AppSettings()

# Configuration for different chains
HLConfigs = {
    "bot_token": "YOUR_HL_BOT_TOKEN",
    "chat_id": "YOUR_HL_CHAT_ID",
    "chain_name": "Hyperliquid",
}

SolConfigs = {
    "bot_token": "YOUR_SOL_BOT_TOKEN",
    "chat_id": "YOUR_SOL_CHAT_ID",
    "chain_name": "Solana",
}


async def main():
    """Main blockchain monitoring application."""

    # Create database writer
    db_writer = PostgresWriter()

    # Create Hyperliquid pipeline
    pipeline_hyperliquid = CoreTransactionPipeline(
        db_writer=db_writer,
        model_routers=[],
        heuristic_routers=[
            VolumeRouter(threshold=10000),
            BatchedWalletTransactionRouter(batch_threshold=5, time_window=300),
            SizeRouter(size_threshold=100),
        ],
        alert_router=TelegramAlertRouter(HLConfigs),
    )

    # Create Solana pipeline
    # pipeline_solana = CoreTransactionPipeline(
    #     db_writer=db_writer,
    #     model_routers=[XGBoostModelSOL()],
    #     heuristic_routers=[
    #         BatchedWalletTransactionRouter(batch_threshold=3, time_window=300),
    #         SizeRouter(size_threshold=50),
    #     ],
    #     alert_router=TelegramAlertRouter(SolConfigs),
    # )

    coinmarketcap_client = CoinMarketCapClient(
        api_key=settings.coinmarketcap_api_key,
        base_url=settings.coinmarketcap_base_url,
    )

    # Create DexScreener client
    # dex_screener_client = DexScreenerClient()
    # # Create Solana transaction fetcher
    # solana_transaction_fetcher = SolanaTransactionFetcher(
    #     settings.solana_rpc_url, dex_screener_client
    # )

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


if __name__ == "__main__":
    asyncio.run(main())
