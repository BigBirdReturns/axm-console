"""The console — one seat that ties the proven parts together.

    pick a surface → drive its spoke to a sealed shard → verify DETACHED →
    plain-English receipt → admit to your review queue.

The console owns the operator experience. It owns no custody: sealing stays in
the spoke (through genesis), verification is the kernel's, and the review queue
records human decisions without making any.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple

from .queue import ReviewQueue
from .receipt import Receipt, build_receipt
from .surfaces import SurfaceRun, get


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class Console:
    """The operator's seat. ``home`` holds the review-queue ledger and staged runs."""

    home: Path

    def __post_init__(self) -> None:
        self.home = Path(self.home)
        self.home.mkdir(parents=True, exist_ok=True)

    @property
    def queue(self) -> ReviewQueue:
        return ReviewQueue(self.home / "review_queue.jsonl")

    def run_surface(self, surface_name: str, *, params: Optional[Dict[str, str]] = None,
                    admit: bool = True) -> Tuple[Receipt, Path]:
        """Drive a surface to a sealed shard, verify it detached, build the
        receipt, and (by default) admit it to the review queue. Returns
        (receipt, shard_dir)."""
        surface = get(surface_name)
        run = SurfaceRun(
            surface=surface_name,
            workdir=self.home / "runs" / f"{surface_name}-{_now().replace(':', '').replace('-', '')}",
            params=params or {},
        )
        shard_dir, trusted_key = surface.run(run)
        receipt = build_receipt(shard_dir, trusted_key)
        if admit and receipt.verified:
            self.queue.admit(receipt, surface=surface_name, at=_now())
        return receipt, shard_dir

    def verify_shard(self, shard_dir: str | Path, trusted_key: str | Path) -> Receipt:
        """Verify any sealed shard detached and build its receipt — no surface
        needed. This is the console's core: hand it a shard from any spoke."""
        return build_receipt(shard_dir, trusted_key)

    def review(self, shard_id: str, *, reviewer: str, disposition: str, note: str = "") -> None:
        self.queue.review(shard_id, reviewer=reviewer, disposition=disposition, note=note, at=_now())
