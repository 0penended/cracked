from fastapi import APIRouter, Request
from datetime import datetime
from zoneinfo import ZoneInfo


router = APIRouter()


@router.post("/notify_websocket_status")
async def monitor_notify(request: Request):
    """Send a status snapshot to Telegram. Intended for cron pings."""
    if not hasattr(request.app.state, "blockchain_service"):
        return {"ok": False, "error": "service_not_initialized"}

    service = request.app.state.blockchain_service
    status = service.get_status()

    # Use Telegram client already constructed in the service
    if not service.telegram_client:
        return {"ok": False, "error": "telegram_not_initialized"}

    # Compose message
    hl = status.get("hyperliquid") or {}
    sol = status.get("solana") or {}

    def fmt_pst(ts):
        if not ts:
            return "n/a"
        try:
            return datetime.fromtimestamp(
                float(ts), ZoneInfo("America/Los_Angeles")
            ).strftime("%Y-%m-%d %H:%M:%S %Z")
        except Exception:
            return str(ts)

    msg = (
        "Blockchain Monitor Status\n"
        f"Service running: {status.get('service_running')}\n"
        f"Hyperliquid running: {hl.get('running')} | wallets: {len(hl.get('subscribed_wallets') or [])} | last_evt: {fmt_pst(hl.get('last_event_ts'))}\n"
        f"Solana running: {sol.get('running')} | wallets: {len(sol.get('subscribed_wallets') or [])} | last_evt: {fmt_pst(sol.get('last_event_ts'))}"
    )

    await service.telegram_client.send_message_async(
        msg, chat_id=service.settings.telegram_chat_id
    )
    return {"ok": True}
