import json
import logging
import subprocess
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class BlockchainService:
    def __init__(self) -> None:
        self.enabled = settings.blockchain_enabled
        self.script = Path(settings.blockchain_client_script)

    def _run(self, args: list[str]) -> str:
        if not self.enabled:
            return "mock_tx_disabled_blockchain"

        try:
            result = subprocess.run(
                ["node", str(self.script), *args],
                capture_output=True,
                text=True,
                check=True,
            )
            parsed = json.loads(result.stdout)
            tx_hash = parsed.get("txHash", "")
            return tx_hash or "mock_tx_empty_hash"
        except Exception:
            logger.exception("Blockchain call failed args=%s. Falling back to mock hash.", args)
            return "mock_tx_blockchain_unavailable"

    def register_property(self, property_id: int, total_shares: int) -> str:
        return self._run(["createProperty", str(property_id), str(total_shares)])

    def buy_primary(self, property_id: int, wallet_address: str, shares: int) -> str:
        return self._run(["buyShares", str(property_id), wallet_address, str(shares)])

    def transfer_secondary(self, property_id: int, from_wallet: str, to_wallet: str, shares: int) -> str:
        return self._run(["transferShares", str(property_id), from_wallet, to_wallet, str(shares)])

    def payout_roi(self, property_id: int, investor_wallet: str, amount_wei: int) -> str:
        return self._run(["payout", str(property_id), investor_wallet, str(amount_wei)])


blockchain_service = BlockchainService()
