"""Utilities for parsing and validating payment headers."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class InsufficientFundsDetails:
    required: Optional[int]
    pay_to: Optional[str]
    asset: Optional[str]


class PaymentHandler:
    """Mirrors the TypeScript PaymentHandler, focused on x-payment payloads."""

    header_key = "x-payment"

    def parse_x402(self, header_value: str) -> Dict[str, Any]:
        """Decode a base64 JSON payload."""
        decoded = base64.b64decode(header_value)
        return json.loads(decoded)

    def is_insufficient_funds(self, payload: Dict[str, Any]) -> bool:
        return payload.get("error") == "insufficient_funds"

    def _first_accept(self, payload: Dict[str, Any]) -> Dict[str, Any] | None:
        accepts = payload.get("accepts") or []
        return accepts[0] if accepts else None

    def get_required_amount(self, payload: Dict[str, Any]) -> Optional[int]:
        accept = self._first_accept(payload)
        if not accept or accept.get("maxAmountRequired") is None:
            return None
        return int(accept["maxAmountRequired"])

    def get_pay_to(self, payload: Dict[str, Any]) -> Optional[str]:
        accept = self._first_accept(payload)
        return accept.get("payTo") if accept else None

    def get_asset(self, payload: Dict[str, Any]) -> Optional[str]:
        accept = self._first_accept(payload)
        return accept.get("asset") if accept else None

    def get_details(self, payload: Dict[str, Any]) -> InsufficientFundsDetails:
        return InsufficientFundsDetails(
            required=self.get_required_amount(payload),
            pay_to=self.get_pay_to(payload),
            asset=self.get_asset(payload),
        )

