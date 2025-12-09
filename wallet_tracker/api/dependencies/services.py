from wallet_tracker.services.price_sync import TokenPriceSyncService
from wallet_tracker.clients.DexScreenerClient import DexScreenerClient
from wallet_tracker.clients.CoinMarketCapClient import CoinMarketCapClient
from wallet_tracker.clients.BigQueryClient import BigQueryClient
from wallet_tracker.core.settings.app import AppSettings


def get_token_price_sync_service() -> TokenPriceSyncService:
    """Dependency to create TokenPriceSyncService with all required clients."""
    settings = AppSettings()

    dex_screener_client = DexScreenerClient()
    coinmarketcap_client = CoinMarketCapClient(
        api_key=settings.coinmarketcap_api_key,
        base_url=settings.coinmarketcap_base_url,
    )
    bigquery_client = BigQueryClient()

    return TokenPriceSyncService(
        dex_screener_client=dex_screener_client,
        coinmarketcap_client=coinmarketcap_client,
        bigquery_client=bigquery_client,
        settings=settings,
    )
