import httpx
from typing import List, Dict, Optional, Any


class CoinMarketCapClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = "https://pro-api.coinmarketcap.com"
        self.client = httpx.Client(
            headers={
                "Accepts": "application/json",
                "X-CMC_PRO_API_KEY": self.api_key,
            }
        )

    def get_prices(
        self, symbols: List[str], convert: str = "USD"
    ) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/v1/cryptocurrency/quotes/latest"
        params = {
            "symbol": ",".join(symbols),
            "convert": convert,
        }

        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Return the full data structure since it's keyed by numeric IDs
            return data.get("data", {})

        except httpx.HTTPError as e:
            print(f"[CMC] HTTP error: {e}")
            return None
        except Exception as e:
            print(f"[CMC] Unexpected error: {e}")
            return None
