from typing import Dict, Any
from pydantic import BaseSettings


class BlockchainSettings(BaseSettings):
    """Settings for blockchain monitoring."""
    
    # Telegram Configuration
    telegram_bot_token_hl: str = ""
    telegram_chat_id_hl: str = ""
    telegram_bot_token_sol: str = ""
    telegram_chat_id_sol: str = ""
    
    # Solana Configuration
    solana_rpc_url: str = "https://api.mainnet-beta.solana.com"
    solana_ws_url: str = "wss://api.mainnet-beta.solana.com/"
    
    # Hyperliquid Configuration
    hyperliquid_ws_url: str = "wss://api.hyperliquid.xyz/ws"
    
    # Monitoring Configuration
    volume_threshold_hl: float = 10000.0
    volume_threshold_sol: float = 5000.0
    batch_threshold_hl: int = 5
    batch_threshold_sol: int = 3
    time_window_seconds: int = 300
    size_threshold_hl: float = 100.0
    size_threshold_sol: float = 50.0
    
    # Database Configuration
    enable_database_logging: bool = True
    
    class Config:
        env_prefix = "BLOCKCHAIN_"
        case_sensitive = False
    
    def get_hl_config(self) -> Dict[str, Any]:
        """Get Hyperliquid configuration."""
        return {
            "bot_token": self.telegram_bot_token_hl,
            "chat_id": self.telegram_chat_id_hl,
            "chain_name": "Hyperliquid"
        }
    
    def get_sol_config(self) -> Dict[str, Any]:
        """Get Solana configuration."""
        return {
            "bot_token": self.telegram_bot_token_sol,
            "chat_id": self.telegram_chat_id_sol,
            "chain_name": "Solana"
        } 