"""AXM Operator Console — core proven independent of any spoke.

The console core (verify-detached → receipt → review queue) is exercised over a
tiny shard sealed with the genesis kernel directly, so these tests need no spoke
repo. Kernel-dependent tests skip cleanly without axm-build / axm-verify.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from axm_console import Console, Disposition, ReviewQueue, VerifyStatus, build_receipt
from axm_console.queue import QueueError
from axm_console.receipt import kernel_available
from axm_console.surfaces import Status, all_surfaces, get

requires_kernel = pytest.mark.skipif(
    not kernel_available(), reason="axm-genesis kernel not on PATH"
)


def _seal_tiny_shard(work: Path, *, tier: str = "pixel_capture") -> tuple[Path, Path]:
    """Seal a minimal shard carrying an evidence tier, via genesis directly."""
    content = work / "content"
    content.mkdir(parents=True, exist_ok=True)
    (content / "capture_manifest.json").write_text(json.dumps({
        "evidence_tier": tier,
        "evidence_tier_limits": ["rendered surface only", "not platform truth"],
    }), encoding="utf-8")
    src = "the operator captured a rendered surface\n"
    (content / "source.txt").write_text(src, encoding="utf-8")
    cands = [
        {"type": "entity", "namespace": "console/test", "label": "surface", "entity_type": "surface"},
        {"type": "entity", "namespace": "console/test", "label": "operator", "entity_type": "actor"},
        {"type": "claim", "subject_label": "operator", "predicate": "captured", "object_label": "surface",
         "object_type": "entity", "tier": 1,
         "evidence": {"source_file": "source.txt", "byte_start": 0, "byte_end": len(src.encode()) - 1, "text": src.strip()}},
    ]
    (work / "c.jsonl").write_text("\n".join(json.dumps(c) for c in cands) + "\n", encoding="utf-8")
    subprocess.run(["axm-build", "keygen", str(work / "keys"), "--name", "pub"], check=True, capture_output=True, text=True)
    shard = work / "shard"
    subprocess.run(["axm-build", "compile", str(work / "c.jsonl"), str(content), str(shard),
                    "--private-key", str(work / "keys" / "pub.key"), "--namespace", "console/test",
                    "--title", "test capture", "--created-at", "2026-07-06T00:00:00Z"],
                   check=True, capture_output=True, text=True)
    return shard, work / "keys" / "pub.pub"


# ── receipt: verify detached, read the tier ──────────────────────────────


@requires_kernel
def test_receipt_verifies_detached_and_reads_tier(tmp_path):
    shard, pub = _seal_tiny_shard(tmp_path)
    r = build_receipt(shard, pub)
    assert r.verified and r.status is VerifyStatus.PASS
    assert r.shard_id.startswith("sh1_") and r.suite == "axm-hybrid1"
    assert r.evidence_tier == "pixel_capture"
    assert "not platform truth" in r.tier_limits
    assert "the vendor / platform" in r.detached_absent
    assert "PASS" in r.render() and "sh1_" in r.render()


@requires_kernel
def test_wrong_key_fails_and_missing_key_refuses(tmp_path):
    shard, _pub = _seal_tiny_shard(tmp_path)
    subprocess.run(["axm-build", "keygen", str(tmp_path / "atk"), "--name", "atk"], check=True, capture_output=True, text=True)
    assert build_receipt(shard, tmp_path / "atk" / "atk.pub").status is VerifyStatus.FAIL
    assert build_receipt(shard, None).status is VerifyStatus.NO_TRUSTED_KEY


def test_missing_manifest_is_not_a_shard(tmp_path):
    with pytest.raises(FileNotFoundError):
        build_receipt(tmp_path, None)


def test_receipt_renders_when_shard_id_unavailable():
    # KERNEL_ABSENT must degrade gracefully: a receipt with no derivable shard id
    # still renders and serializes instead of crashing.
    from axm_console.receipt import Receipt

    r = Receipt(shard_id=None, shard_dir="/x", status=VerifyStatus.KERNEL_ABSENT,
                evidence_tier=None, tier_limits=[], suite=None, title=None, sealed_at=None)
    assert not r.verified
    assert "unavailable" in r.render() and "KERNEL_ABSENT" in r.render()
    assert r.to_dict()["shard_id"] is None


# ── queue: verified-only, attention-only, append-only ────────────────────


@requires_kernel
def test_queue_admits_verified_and_records_disposition(tmp_path):
    shard, pub = _seal_tiny_shard(tmp_path)
    r = build_receipt(shard, pub)
    q = ReviewQueue(tmp_path / "q.jsonl")
    q.admit(r, surface="screenshot", at="2026-07-06T00:00:00Z")
    assert len(q.pending()) == 1
    q.review(r.shard_id, reviewer="bigbird", disposition="escalate", at="2026-07-06T00:01:00Z")
    items = q.items()
    assert len(items) == 1 and items[0].reviewed and items[0].disposition == "escalate"
    assert q.pending() == []


def test_queue_refuses_unverified(tmp_path):
    from axm_console.receipt import Receipt

    bad = Receipt(shard_id="sh1_x", shard_dir=str(tmp_path), status=VerifyStatus.FAIL,
                  evidence_tier="pixel_capture", tier_limits=[], suite="axm-hybrid1",
                  title="t", sealed_at=None)
    with pytest.raises(QueueError, match="did not verify"):
        ReviewQueue(tmp_path / "q.jsonl").admit(bad, surface="screenshot", at="t")


def test_queue_refuses_truth_verdicts_and_requires_human(tmp_path):
    from axm_console.receipt import Receipt

    ok = Receipt(shard_id="sh1_ok", shard_dir=str(tmp_path), status=VerifyStatus.PASS,
                 evidence_tier="pixel_capture", tier_limits=[], suite="axm-hybrid1",
                 title="t", sealed_at=None)
    q = ReviewQueue(tmp_path / "q.jsonl")
    q.admit(ok, surface="screenshot", at="t")
    for bad in ("authentic", "true", "verified_content"):
        with pytest.raises(QueueError, match="not representable"):
            q.review("sh1_ok", reviewer="x", disposition=bad, at="t")
    with pytest.raises(QueueError, match="human reviewer"):
        q.review("sh1_ok", reviewer="  ", disposition="dismiss", at="t")
    assert {d.value for d in Disposition} == {"escalate", "dismiss", "needs_context"}


def test_queue_is_append_only(tmp_path):
    from axm_console.receipt import Receipt

    ok = Receipt(shard_id="sh1_ok", shard_dir=str(tmp_path), status=VerifyStatus.PASS,
                 evidence_tier="pixel_capture", tier_limits=[], suite="axm-hybrid1", title="t", sealed_at=None)
    q = ReviewQueue(tmp_path / "q.jsonl")
    q.admit(ok, surface="screenshot", at="t")
    q.review("sh1_ok", reviewer="a", disposition="needs_context", at="t1")
    q.review("sh1_ok", reviewer="b", disposition="escalate", at="t2")
    rows = (tmp_path / "q.jsonl").read_text().splitlines()
    assert len(rows) == 3  # nothing overwritten
    assert q.items()[0].disposition == "escalate"  # latest wins for display


# ── surfaces: honest driven-vs-declared ──────────────────────────────────


def test_surface_registry_is_all_driven():
    names = {s.name for s in all_surfaces()}
    assert {"camera-frames", "screenshot", "interface-procedure", "foundry-export",
            "ontology-exit"} <= names
    assert all(get(n).status is Status.DRIVEN for n in names)  # every surface now driven


def test_a_declared_surface_would_refuse_rather_than_fake(tmp_path):
    # The refusal contract still holds for any future DECLARED surface: it raises
    # rather than faking a capture.
    from axm_console.surfaces import Status, Surface, SurfaceRun

    declared = Surface(name="future-x", verb="capture", owner_repo="axm-future",
                       tier="future_tier", status=Status.DECLARED, summary="not wired")
    with pytest.raises(NotImplementedError, match="DECLARED, not driven"):
        declared.run(SurfaceRun("future-x", tmp_path, {}))


# ── end to end through the Console object ────────────────────────────────


@requires_kernel
def test_console_verify_and_review_roundtrip(tmp_path):
    shard, pub = _seal_tiny_shard(tmp_path)
    console = Console(tmp_path / "home")
    receipt = console.verify_shard(shard, pub)
    assert receipt.verified
    console.queue.admit(receipt, surface="screenshot", at="2026-07-06T00:00:00Z")
    console.review(receipt.shard_id, reviewer="bigbird", disposition="dismiss", note="benign")
    item = console.queue.items()[0]
    assert item.reviewed and item.disposition == "dismiss" and item.reviewer == "bigbird"
