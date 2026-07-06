"""Surface drivers — each DRIVEN surface, end to end through the console.

These are integration tests: they drive a real spoke to a sealed shard and have
the console verify it DETACHED. They need the spoke checked out, so each skips
cleanly when its repo isn't present (resolve via AXM_*_REPO env, else the
deployment default). In CI (kernel only, no spokes) they all skip; the
spoke-independent core suite in test_console.py still runs. Where the spokes ARE
present (a full workspace), all four surfaces are exercised for real.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from axm_console import Console
from axm_console.receipt import kernel_available

pytestmark = pytest.mark.skipif(not kernel_available(), reason="axm-genesis kernel not on PATH")


def _spoke(env_var: str, default: str, marker: str) -> str | None:
    repo = Path(os.environ.get(env_var, default))
    return str(repo) if (repo / marker).exists() else None


CAMERA = _spoke("AXM_EMBODIED_REPO", "/workspace/axm-embodied", "src/axm_embodied/frame_capture.py")
SG = _spoke("AXM_SCREENGHOST_REPO", "/workspace/screenghost", "core/pixel_seal.py")
CORE = _spoke("AXM_CORE_REPO", "/workspace/axm-core", "foundry_exit/sim_surface.py")


def _drive(tmp_path, name, params):
    receipt, shard = Console(tmp_path / "home").run_surface(name, params=params, admit=True)
    return receipt


@pytest.mark.skipif(not CAMERA, reason="axm-embodied spoke not present")
def test_camera_frames_driven(tmp_path):
    r = _drive(tmp_path, "camera-frames", {"spoke_repo": CAMERA})
    assert r.verified and r.evidence_tier == "physical_capture" and r.shard_id.startswith("sh1_")


@pytest.mark.skipif(not SG, reason="ScreenGhost spoke not present")
def test_screenshot_driven(tmp_path):
    r = _drive(tmp_path, "screenshot", {"spoke_repo": SG})
    assert r.verified and r.evidence_tier == "pixel_capture"


@pytest.mark.skipif(not SG, reason="ScreenGhost spoke not present")
def test_synthesized_screenshot_is_labeled_honestly(tmp_path):
    import json

    # No png_path -> a synthesized placeholder. It must NOT be sealed as a real
    # manual screenshot; the sealed manifest must say what it is.
    receipt, shard = Console(tmp_path / "home").run_surface("screenshot", params={"spoke_repo": SG})
    manifest = json.loads((Path(shard) / "content" / "pixel_capture_manifest.json").read_text())
    assert manifest["capture_method"] == "synthesized_sample"
    assert manifest["capture_method"] != "manual_screenshot"
    assert "synthesized sample" in manifest["source_label"]


@pytest.mark.skipif(not SG, reason="ScreenGhost spoke not present")
def test_interface_procedure_driven(tmp_path):
    try:
        import playwright  # noqa: F401
    except ImportError:
        pytest.skip("playwright not installed")
    r = _drive(tmp_path, "interface-procedure", {"spoke_repo": SG})
    assert r.verified and r.evidence_tier == "interface_procedure_trace"


@pytest.mark.skipif(not CORE, reason="axm-core spoke not present")
def test_foundry_export_driven(tmp_path):
    # Foundry seals a real, verifiable bundle; its manifest carries no embedded
    # evidence_tier, so the console honestly reports it as unstated rather than
    # inventing one. The record still verifies detached.
    r = _drive(tmp_path, "foundry-export", {"spoke_repo": CORE, "objects": "80"})
    assert r.verified and r.shard_id.startswith("sh1_")
    assert r.evidence_tier is None  # honestly unstated by the sealed bundle


@pytest.mark.skipif(not (CAMERA and SG and CORE), reason="not all spokes present")
def test_all_surfaces_land_in_one_queue(tmp_path):
    console = Console(tmp_path / "home")
    console.run_surface("camera-frames", params={"spoke_repo": CAMERA})
    console.run_surface("screenshot", params={"spoke_repo": SG})
    console.run_surface("foundry-export", params={"spoke_repo": CORE, "objects": "40"})
    tiers = {i.evidence_tier for i in console.queue.items()}
    assert "physical_capture" in tiers and "pixel_capture" in tiers
    assert len(console.queue.pending()) == 3  # all admitted, all awaiting your review
