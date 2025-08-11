import time
from collections import defaultdict, deque
from typing import Deque, Dict


class WalletActivityLimiter:
    """Tracks per-wallet activity in a sliding window and flags high-activity wallets.

    - Maintains a deque of timestamps per wallet
    - Prunes entries older than `activity_window_seconds`
    - Marks wallet as blacklisted if entries exceed `max_tx_per_window`
    """

    def __init__(
        self,
        activity_window_seconds: int = 60,
        max_tx_per_window: int = 15,
        blacklist_ttl_seconds: int = 2 * 60 * 60,  # 2 hours
    ) -> None:
        self.activity_window_seconds = activity_window_seconds
        self.max_tx_per_window = max_tx_per_window
        self.blacklist_ttl_seconds = blacklist_ttl_seconds
        self._wallet_activity: Dict[str, Deque[float]] = defaultdict(deque)
        # Map wallet -> blacklisted_at timestamp
        self._blacklisted_wallets: Dict[str, float] = {}

    def is_blacklisted(self, wallet: str) -> bool:
        ts = self._blacklisted_wallets.get(wallet)
        if ts is None:
            return False
        # Expire blacklists after TTL
        now = time.time()
        if now - ts > self.blacklist_ttl_seconds:
            del self._blacklisted_wallets[wallet]
            return False
        return True

    def record_and_check(self, wallet: str, qualifying: bool = True) -> bool:
        """Record activity for wallet and return True if wallet is blacklisted.

        Returns True if the wallet is newly blacklisted due to threshold breach
        or is already blacklisted.
        """
        # Respect TTL-based blacklist
        if self.is_blacklisted(wallet):
            return True

        # If this transaction should not count toward blacklisting, skip recording
        if not qualifying:
            return False

        now = time.time()
        activity = self._wallet_activity[wallet]

        # Append and prune outside the window
        activity.append(now)
        cutoff = now - self.activity_window_seconds
        while activity and activity[0] < cutoff:
            activity.popleft()

        # Blacklist if threshold exceeded
        if len(activity) > self.max_tx_per_window:
            self._blacklisted_wallets[wallet] = now
            return True

        return False
