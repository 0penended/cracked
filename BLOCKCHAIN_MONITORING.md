# Blockchain Monitoring System

This system provides real-time monitoring of blockchain transactions across multiple chains (Solana, Hyperliquid) with ML model evaluation, heuristic-based alerts, and Telegram notifications.

## Architecture Overview

The system follows a modular architecture with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Solana        │    │   Hyperliquid   │    │   Other Chains  │
│   Listener      │    │   Listener      │    │   (Extensible)  │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │   CoreTransactionPipeline │
                    └─────────────┬─────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
    ┌─────▼─────┐         ┌───────▼──────┐         ┌─────▼─────┐
    │ Database  │         │ ML Models &  │         │ Telegram  │
    │ Writer    │         │ Heuristics   │         │ Alerts    │
    └───────────┘         └──────────────┘         └───────────┘
```

## Components

### 1. Domain Models (`app/models/domain/blockchain.py`)

- `UnifiedTransactionEvent`: Normalized transaction data structure
- `ChainListener`: Abstract base class for blockchain listeners
- `ModelRouter`: Abstract base class for ML model evaluation
- `HeuristicRouter`: Abstract base class for rule-based evaluation
- `AlertRouter`: Abstract base class for alert delivery
- `DatabaseWriter`: Abstract base class for data persistence

### 2. Core Pipeline (`app/services/pipeline.py`)

- `CoreTransactionPipeline`: Orchestrates the entire monitoring workflow
- Handles event processing, evaluation, and alerting

### 3. Blockchain Listeners (`app/services/listeners.py`)

- `SolanaListener`: Monitors Solana blockchain transactions
- `HyperliquidListener`: Monitors Hyperliquid trading activity
- Both implement the `ChainListener` ABC

### 4. Routers (`app/services/routers.py`)

- **ML Models**: `XGBoostModelHL`, `XGBoostModelSOL`
- **Heuristics**: `VolumeRouter`, `BatchedWalletTransactionRouter`, `SizeRouter`
- **Alerts**: `TelegramAlertRouter`
- **Database**: `PostgresWriter`

## Setup and Configuration

### 1. Environment Variables

Create a `.env` file with the following variables:

```bash
# Telegram Configuration
BLOCKCHAIN_TELEGRAM_BOT_TOKEN_HL=your_hyperliquid_bot_token
BLOCKCHAIN_TELEGRAM_CHAT_ID_HL=your_hyperliquid_chat_id
BLOCKCHAIN_TELEGRAM_BOT_TOKEN_SOL=your_solana_bot_token
BLOCKCHAIN_TELEGRAM_CHAT_ID_SOL=your_solana_chat_id

# Monitoring Thresholds
BLOCKCHAIN_VOLUME_THRESHOLD_HL=10000.0
BLOCKCHAIN_VOLUME_THRESHOLD_SOL=5000.0
BLOCKCHAIN_BATCH_THRESHOLD_HL=5
BLOCKCHAIN_BATCH_THRESHOLD_SOL=3
BLOCKCHAIN_TIME_WINDOW_SECONDS=300
```

### 2. Dependencies

Add these to your `pyproject.toml`:

```toml
[tool.poetry.dependencies]
solana = "^0.30.2"
websockets = "^11.0.3"
aiohttp = "^3.8.5"
```

### 3. Running the Monitor

```bash
# Run the blockchain monitor
python -m app.blockchain_monitor
```

## Usage Example

```python
from app.blockchain_monitor import main
import asyncio

# Run the monitoring system
asyncio.run(main())
```

## Customization

### Adding New Chains

1. Create a new listener class implementing `ChainListener`
2. Add it to the main monitoring loop
3. Configure chain-specific models and heuristics

### Adding New ML Models

1. Create a class implementing `ModelRouter`
2. Implement the `should_alert` method
3. Add to the pipeline configuration

### Adding New Heuristics

1. Create a class implementing `HeuristicRouter`
2. Implement the `should_alert` method
3. Add to the pipeline configuration

### Adding New Alert Channels

1. Create a class implementing `AlertRouter`
2. Implement the `send` method
3. Configure in the pipeline

## Database Integration

The system is designed to integrate with your existing PostgreSQL database. The `PostgresWriter` class can be extended to use your existing transaction models and services.

## Monitoring and Logging

The system provides comprehensive logging for:

- Connection status
- Transaction processing
- Alert triggers
- Error handling

## Security Considerations

- Store sensitive configuration in environment variables
- Use secure WebSocket connections
- Implement rate limiting for API calls
- Validate all incoming transaction data

## Performance Optimization

- Use connection pooling for database operations
- Implement caching for frequently accessed data
- Use async/await for non-blocking operations
- Consider horizontal scaling for high-volume monitoring
