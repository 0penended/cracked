from typing import List, Dict, Any
from google.cloud import bigquery
from loguru import logger


class BigQueryClient:
    """Client for BigQuery operations."""

    def __init__(self, project_id: str = None):
        self.client = bigquery.Client(project=project_id)

    async def get_positions_tokens(
        self, dataset_id: str, table_id: str
    ) -> List[Dict[str, Any]]:
        """Get distinct token addresses and exchanges from positions table."""
        try:
            query = f"""
            SELECT DISTINCT token_ca, exchange 
            FROM `{self.client.project}.{dataset_id}.{table_id}`
            WHERE snapshot_date = CURRENT_DATE()
            AND token_ca IS NOT NULL
            """

            logger.info(f"Executing BigQuery query: {query}")

            # Execute the query
            query_job = self.client.query(query)
            results = query_job.result()

            positions = []
            for row in results:
                positions.append({"token_ca": row.token_ca, "exchange": row.exchange})

            logger.info(
                f"Retrieved {len(positions)} distinct token positions from BigQuery"
            )
            return positions

        except Exception as e:
            logger.error(f"Error reading from BigQuery positions table: {e}")
            raise

    async def write_coin_prices(
        self, dataset_id: str, table_id: str, prices: List[Dict[str, Any]]
    ) -> None:
        """Write price data to coin_prices table."""
        if not prices:
            logger.info("No prices to write to BigQuery")
            return

        try:
            table_ref = f"{self.client.project}.{dataset_id}.{table_id}"

            # Prepare the data for BigQuery
            rows_to_insert = []
            for price in prices:
                row = {
                    "token_ca": price["token_ca"],
                    "symbol": price["symbol"],
                    "price_date": price["price_date"].isoformat(),
                    "price_usd": price["price_usd"],
                    "price_1h_delta_pct": price["price_1h_delta_pct"],
                    "price_24h_delta_pct": price["price_24h_delta_pct"],
                    "volume_24h_usd": price["volume_24h_usd"],
                    "liquidity_usd": price["liquidity_usd"],
                    "market_cap_usd": price["market_cap_usd"],
                    "source": price["source"],
                    "last_updated": price["last_updated"].isoformat(),
                }
                rows_to_insert.append(row)

            # Insert the data
            errors = self.client.insert_rows_json(table_ref, rows_to_insert)

            if errors:
                logger.error(f"Errors inserting rows to BigQuery: {errors}")
                raise Exception(f"BigQuery insert errors: {errors}")

            logger.info(
                f"Successfully wrote {len(prices)} price records to BigQuery table {table_ref}"
            )

        except Exception as e:
            logger.error(f"Error writing to BigQuery coin_prices table: {e}")
            raise
