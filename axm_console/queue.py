"""The operator review queue — where sealed records wait for YOUR decision.

Every record the console admits was verified detached first (a non-verified
record is refused, never queued). A human then records an attention disposition;
the console stores the decision and decides nothing itself. This mirrors the
landed GhostBox review discipline — attention-only vocabulary, human-attributed,
append-only — reimplemented here so the console imports no spoke.

Persistence is a plain append-only JSONL ledger: one line per admission, one per
decision. It is auditable by eye and re-readable without this code.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .receipt import Receipt


class Disposition(str, Enum):
    """Attention-shaped, never truth-shaped. There is no 'authentic', no 'true':
    a review moves attention, it never adjudicates the record's meaning or
    upgrades its tier."""

    ESCALATE = "escalate"
    DISMISS = "dismiss"
    NEEDS_CONTEXT = "needs_context"


class QueueError(RuntimeError):
    pass


@dataclass(frozen=True)
class QueueItem:
    shard_id: str
    evidence_tier: Optional[str]
    title: Optional[str]
    surface: str
    shard_dir: str
    admitted_at: str
    reviewed: bool
    disposition: Optional[str]
    reviewer: Optional[str]
    note: Optional[str]


class ReviewQueue:
    """Append-only queue backed by a JSONL ledger."""

    def __init__(self, ledger_path: str | Path) -> None:
        self._path = Path(ledger_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _append(self, row: dict) -> None:
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, sort_keys=True) + "\n")

    def _rows(self) -> List[dict]:
        if not self._path.exists():
            return []
        return [json.loads(l) for l in self._path.read_text(encoding="utf-8").splitlines() if l.strip()]

    def admit(self, receipt: Receipt, *, surface: str, at: str) -> str:
        """Admit a VERIFIED record for review. A non-verified record is refused."""
        if not receipt.verified:
            raise QueueError(
                f"shard {receipt.shard_id} did not verify (status={receipt.status.value}); "
                f"the console does not queue unverified records."
            )
        self._append({
            "kind": "admit",
            "shard_id": receipt.shard_id,
            "evidence_tier": receipt.evidence_tier,
            "title": receipt.title,
            "surface": surface,
            "shard_dir": receipt.shard_dir,
            "at": at,
        })
        return receipt.shard_id

    def review(self, shard_id: str, *, reviewer: str, disposition: "Disposition | str",
               note: str = "", at: str) -> None:
        """Record one human decision. Append-only; nothing is edited or replaced."""
        if not any(r["kind"] == "admit" and r["shard_id"] == shard_id for r in self._rows()):
            raise QueueError(f"shard {shard_id} was never admitted for review.")
        if not (isinstance(reviewer, str) and reviewer.strip()):
            raise QueueError("a review must be attributed to a human reviewer.")
        try:
            disp = Disposition(disposition)
        except ValueError:
            raise QueueError(
                f"{disposition!r} is not an attention disposition "
                f"({[d.value for d in Disposition]}); truth-shaped verdicts are not representable."
            )
        self._append({
            "kind": "review", "shard_id": shard_id, "disposition": disp.value,
            "reviewer": reviewer, "note": note, "at": at,
        })

    def items(self) -> List[QueueItem]:
        """Current state folded from the ledger. Latest review wins for display;
        the full history stays in the ledger."""
        admits: Dict[str, dict] = {}
        latest_review: Dict[str, dict] = {}
        for r in self._rows():
            if r["kind"] == "admit":
                admits.setdefault(r["shard_id"], r)
            elif r["kind"] == "review":
                latest_review[r["shard_id"]] = r
        out = []
        for sid, a in admits.items():
            rv = latest_review.get(sid)
            out.append(QueueItem(
                shard_id=sid, evidence_tier=a.get("evidence_tier"), title=a.get("title"),
                surface=a.get("surface", "?"), shard_dir=a.get("shard_dir", ""),
                admitted_at=a.get("at", "?"), reviewed=rv is not None,
                disposition=rv["disposition"] if rv else None,
                reviewer=rv["reviewer"] if rv else None, note=rv["note"] if rv else None,
            ))
        return out

    def pending(self) -> List[QueueItem]:
        return [i for i in self.items() if not i.reviewed]

    def render(self) -> str:
        items = self.items()
        if not items:
            return "review queue is empty."
        pend = sum(1 for i in items if not i.reviewed)
        lines = [f"REVIEW QUEUE — {len(items)} record(s), {pend} pending", "─" * 66]
        for i in items:
            state = f"→ {i.disposition} ({i.reviewer})" if i.reviewed else "● PENDING REVIEW"
            lines.append(f"  {i.shard_id[:18]}…  [{i.evidence_tier or '?'}]  via {i.surface}")
            lines.append(f"      {i.title or ''}")
            lines.append(f"      {state}")
        lines.append("─" * 66)
        return "\n".join(lines)
