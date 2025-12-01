"""Entrypoint for PA Engine trading system."""

import yaml
import time
from pathlib import Path
from typing import Optional

from pa_engine.core.config_models import AppConfig, ThresholdConfig, RiskConfig
from pa_engine.data.ohlcv_client import OhlcvClient, HyperliquidOhlcvClient, CcxtOhlcvClient
from pa_engine.jobs.signal_job import SignalJob


def load_config(config_dir: Optional[Path] = None) -> AppConfig:
    """
    Load configuration from YAML files.
    
    Args:
        config_dir: Directory containing config files (default: ./config)
        
    Returns:
        AppConfig object
    """
    if config_dir is None:
        config_dir = Path(__file__).parent / "config"
    
    # Load thresholds
    thresholds_path = config_dir / "thresholds.yaml"
    with open(thresholds_path, "r") as f:
        thresholds_data = yaml.safe_load(f)
    
    thresholds = ThresholdConfig(**thresholds_data["thresholds"])
    risk = RiskConfig(**thresholds_data["risk"])
    
    # Load assets
    assets_path = config_dir / "assets.yaml"
    with open(assets_path, "r") as f:
        assets_data = yaml.safe_load(f)
    
    symbols = assets_data["symbols"]
    
    return AppConfig(
        symbols=symbols,
        timeframe=thresholds_data["app"]["timeframe"],
        history_lookback_days=thresholds_data["app"]["history_lookback_days"],
        thresholds=thresholds,
        risk=risk
    )


def main():
    """Main entrypoint - runs signal generation."""
    cfg = load_config()
    # Use Hyperliquid client by default
    client: OhlcvClient = HyperliquidOhlcvClient()
    job = SignalJob(cfg, client)

    print(f"Running signal job for {len(cfg.symbols)} symbols...")
    recs = job.run_once()
    
    if recs:
        print(f"\nGenerated {len(recs)} trade recommendations:")
        for r in recs:
            print(f"\n{r.symbol} ({r.timestamp})")
            print(f"  Side: {r.side}")
            print(f"  Entry: {r.entry:.2f}")
            print(f"  Stop Loss: {r.stop_loss:.2f}")
            print(f"  Take Profit: {r.take_profit:.2f}")
            print(f"  Leverage: {r.leverage:.1f}x")
            print(f"  Reason: {r.reason}")
    else:
        print("No trade recommendations generated.")


def run_scheduler(interval_hours: int = 4):
    """
    Run signal job on a schedule.
    
    Args:
        interval_hours: Hours between runs (default: 4)
    """
    cfg = load_config()
    # Use Hyperliquid client by default
    client: OhlcvClient = HyperliquidOhlcvClient()
    job = SignalJob(cfg, client)
    
    interval_seconds = interval_hours * 3600
    
    print(f"Starting scheduler - running every {interval_hours} hours")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Running signal job...")
            recs = job.run_once()
            
            if recs:
                print(f"Generated {len(recs)} trade recommendations")
                for r in recs:
                    print(f"  - {r.symbol}: {r.side} @ {r.entry:.2f}")
            else:
                print("No signals generated")
            
            print(f"Sleeping for {interval_hours} hours...")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("\nScheduler stopped")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--scheduler":
        run_scheduler()
    else:
        main()

