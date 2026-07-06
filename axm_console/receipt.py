"""The operator receipt — the console's one owned contribution.

Given any genesis-sealed shard directory and an out-of-band trusted key, this
verifies the record DETACHED (only the shard bytes + the kernel CLI + the key —
no spoke code, no vendor, no AXM component in the loop) and renders a
plain-English receipt a human can hand to a lawyer, an insurer, or a skeptic.

The console owns nothing cryptographic. It depends on the genesis kernel — the
one legitimate shared root — and on nothing else. It never seals, never mints a
shard id, never rewrites a shard. It reads, verifies, and reports.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

AXM_VERIFY = "axm-verify"

# Human-readable names for the surfaces whose absence a detached verify proves.
_ABSENT = ("the originating spoke", "the vendor / platform", "the browser or sensor", "any AI layer")


class VerifyStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    MALFORMED = "malformed"
    NO_TRUSTED_KEY = "no_trusted_key"
    KERNEL_ABSENT = "kernel_absent"


def kernel_available() -> bool:
    return shutil.which(AXM_VERIFY) is not None


@dataclass(frozen=True)
class Receipt:
    """What one sealed record is, and that it holds without anyone's platform."""

    shard_id: str
    shard_dir: str
    status: VerifyStatus
    evidence_tier: Optional[str]
    tier_limits: List[str]
    suite: Optional[str]
    title: Optional[str]
    sealed_at: Optional[str]
    detached_absent: List[str] = field(default_factory=lambda: list(_ABSENT))

    @property
    def verified(self) -> bool:
        return self.status is VerifyStatus.PASS

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "shard_id": self.shard_id,
            "status": self.status.value,
            "evidence_tier": self.evidence_tier,
            "tier_limits": self.tier_limits,
            "suite": self.suite,
            "title": self.title,
            "sealed_at": self.sealed_at,
            "verified_detached_without": self.detached_absent if self.verified else [],
            "shard_dir": self.shard_dir,
        }
        return d

    def render(self) -> str:
        tick = "PASS ✓" if self.verified else self.status.value.upper()
        lines = [
            "AXM CUSTODY RECEIPT",
            "─" * 60,
            f"  record    {self.title or '(untitled)'}",
            f"  tier      {self.evidence_tier or '(tier unstated)'}",
        ]
        for lim in self.tier_limits:
            lines.append(f"              · {lim}")
        lines += [
            f"  shard id  {self.shard_id}",
            f"  suite     {self.suite or '?'}",
            f"  sealed    {self.sealed_at or '?'}",
            f"  verify    {tick}",
        ]
        if self.verified:
            lines.append("  proven    verifiable with only these bytes + the out-of-band key,")
            lines.append("            after all of the following are removed:")
            for a in self.detached_absent:
                lines.append(f"              — {a}")
        else:
            lines.append("  proven    NOT verified — this record is blocked from trusted use.")
        lines.append("─" * 60)
        return "\n".join(lines)


def _detached_verify(shard_dir: Path, trusted_key: Optional[Path]) -> VerifyStatus:
    """Verify with ONLY the kernel CLI + shard bytes + the out-of-band key."""
    if not kernel_available():
        return VerifyStatus.KERNEL_ABSENT
    if not trusted_key:
        return VerifyStatus.NO_TRUSTED_KEY
    code = subprocess.run(
        [AXM_VERIFY, "shard", str(shard_dir), "--trusted-key", str(trusted_key)],
        capture_output=True, text=True,
    ).returncode
    if code == 0:
        return VerifyStatus.PASS
    if code == 2:
        return VerifyStatus.MALFORMED
    return VerifyStatus.FAIL


def _derive_shard_id(shard_dir: Path) -> str:
    """Genesis derives custody identity; the console never mints it."""
    from axm_verify.crypto import derive_shard_id  # the shared root, lazily

    return derive_shard_id((shard_dir / "manifest.json").read_bytes())


def _read_tier(shard_dir: Path) -> tuple[Optional[str], List[str]]:
    """Find the evidence tier + limits. Spokes name their manifest differently
    (pixel_capture_manifest.json, capture_manifest.json, interface_trace_manifest
    .json, ...), so scan the sealed content for whichever JSON declares a tier."""
    content = shard_dir / "content"
    if content.is_dir():
        for p in sorted(content.glob("*.json")):
            try:
                doc = json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            tier = doc.get("evidence_tier")
            if isinstance(tier, str):
                limits = doc.get("evidence_tier_limits") or []
                return tier, [str(x) for x in limits]
    return None, []


def build_receipt(shard_dir: str | Path, trusted_key: Optional[str | Path]) -> Receipt:
    """Verify a sealed shard detached and assemble its operator receipt."""
    shard_dir = Path(shard_dir)
    manifest_path = shard_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"no genesis manifest at {shard_dir} — not a sealed shard")

    status = _detached_verify(shard_dir, Path(trusted_key) if trusted_key else None)
    manifest = json.loads(manifest_path.read_bytes())
    tier, limits = _read_tier(shard_dir)
    return Receipt(
        shard_id=_derive_shard_id(shard_dir),
        shard_dir=str(shard_dir),
        status=status,
        evidence_tier=tier,
        tier_limits=limits,
        suite=manifest.get("suite"),
        title=(manifest.get("metadata") or {}).get("title") or manifest.get("title"),
        sealed_at=(manifest.get("metadata") or {}).get("created_at"),
    )
