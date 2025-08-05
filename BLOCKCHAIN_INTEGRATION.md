# Blockchain Monitoring Integration

This document explains how the blockchain monitoring functionality is integrated into the FastAPI application.

## Overview

The blockchain monitoring code from `blockchain_monitor.py` has been refactored into a service that runs as a background task when the FastAPI app starts up. This allows you to:

1. **Run blockchain monitoring alongside your API** - No need for separate processes
2. **Serve API endpoints** - Your cron jobs can still ping the endpoints
3. **Clean startup/shutdown** - Proper resource management
4. **Status monitoring** - Check if blockchain monitoring is running

## Architecture

### Components

1. **`BlockchainMonitorService`** (`app/services/blockchain_monitor_service.py`)

   - Wraps the blockchain monitoring logic
   - Manages lifecycle (start/stop)
   - Handles database connections and clients
   - Runs as a background task

2. **FastAPI Integration** (`app/core/events.py`)

   - Starts the service on app startup
   - Stops the service on app shutdown
   - Stores service instance in `app.state`

3. **Status Endpoint** (`app/api/routes/api.py`)
   - `/blockchain-monitor/status` - Check if monitoring is running

## How It Works

### Startup Process

1. When you run `uvicorn app.main:app --reload`:
   - FastAPI app starts
   - Database connection is established
   - `BlockchainMonitorService` is created and started
   - Service runs Solana and Hyperliquid listeners in background
   - API endpoints become available

### Shutdown Process

1. When the app receives a shutdown signal:
   - Blockchain monitoring service is stopped gracefully
   - Database connections are closed
   - All resources are cleaned up

### API Endpoints

- `GET /health` - Basic health check
- `GET /blockchain-monitor/status` - Check blockchain monitoring status
- `GET /cache/stats` - Cache statistics
- `POST /cache/cleanup` - Clean up expired cache entries

## Usage

### Starting the Application

```bash
# Start with blockchain monitoring
uvicorn app.main:app --reload

# Or with specific host/port
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Checking Status

```bash
# Check if blockchain monitoring is running
curl http://localhost:8000/blockchain-monitor/status

# Response:
{
  "status": "running",
  "is_running": true
}
```

### Cron Job Integration

Your cron jobs can still ping the API endpoints:

```bash
# Example cron job
*/5 * * * * curl -X POST http://localhost:8000/cache/cleanup
```

## Error Handling

- If blockchain monitoring fails to start, the API will still be available
- Errors are logged but don't crash the entire application
- The service can be restarted by restarting the FastAPI app

## Testing

You can test the blockchain monitoring service independently:

```bash
python test_blockchain_integration.py
```

## Configuration

The service uses the same configuration as the original `blockchain_monitor.py`:

- Database connection from `DATABASE_URL`
- API keys from environment variables
- Wallet addresses and thresholds from settings

## Benefits

1. **Single Process** - Everything runs in one process
2. **Resource Efficiency** - Shared database connections
3. **Simplified Deployment** - One service to manage
4. **Better Monitoring** - Status endpoint for health checks
5. **Graceful Shutdown** - Proper cleanup on exit
