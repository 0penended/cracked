"""Entrypoint for price action trading application."""

import yaml
from pathlib import Path

from price_action.core.config_models import AppConfig, RiskConfig, ThresholdConfig
from price_action.data.ohlcv_client import BinanceOhlcvClient, OhlcvClient
from price_action.jobs.signal_job import SignalJob


def load_config(config_path: str = "price_action/config/thresholds.yaml") -> AppConfig:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to configuration YAML file

    Returns:
        AppConfig instance
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_file) as f:
        data = yaml.safe_load(f)

    thresholds = ThresholdConfig(**data["thresholds"])
    risk = RiskConfig(**data["risk"])

    return AppConfig(
        symbols=data["symbols"],
        timeframe=data["timeframe"],
        history_lookback_days=data["history_lookback_days"],
        thresholds=thresholds,
        risk=risk,
    )


def main():
    """Main entrypoint for signal generation."""
    # Load configuration
    cfg = load_config()

    # Initialize OHLCV client (Binance for now)
    client: OhlcvClient = BinanceOhlcvClient()

    # Create and run signal job
    job = SignalJob(cfg, client)
    recs = job.run_once()

    # Print recommendations
    print(f"\nGenerated {len(recs)} trade recommendations:\n")
    for r in recs:
        print(f"Symbol: {r.symbol}")
        print(f"  Side: {r.side}")
        print(f"  Entry: ${r.entry:.2f}")
        print(f"  Stop Loss: ${r.stop_loss:.2f}")
        print(f"  Take Profit: ${r.take_profit:.2f}")
        print(f"  Leverage: {r.leverage}x")
        print(f"  Reason: {r.reason}")
        print()


if __name__ == "__main__":
    main()

