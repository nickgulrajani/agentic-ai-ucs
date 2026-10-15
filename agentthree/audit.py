"""SHA-256 hash-chained audit ledger (matches the guide's Live Run semantics)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


def _stable(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, default=str, separators=(",", ":"))


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class AuditLedger:
    def __init__(self, context_id: str, trace_id: str) -> None:
        self.context_id = context_id
        self.trace_id = trace_id
        self.entries: list[dict[str, Any]] = []

    def append(
        self,
        *,
        seq: int,
        agent: str,
        kind: str,
        title: str,
        payload: Any = None,
    ) -> dict[str, Any]:
        body = {
            "seq": seq,
            "ts": datetime.now(timezone.utc).isoformat(),
            "contextId": self.context_id,
            "traceId": self.trace_id,
            "agent": agent,
            "kind": kind,
            "title": title,
            "payloadHash": sha256(_stable(payload if payload is not None else title)),
        }
        prev = self.entries[-1]["hash"] if self.entries else "0" * 64
        body["prevHash"] = prev
        body["hash"] = sha256(_stable(body))
        self.entries.append(body)
        return body
