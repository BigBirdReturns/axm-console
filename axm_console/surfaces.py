"""Surface registry — the assembly layer.

A *surface* is anything the operator can capture or operate: a Foundry export, a
screenshot, a dashboard procedure, a camera trigger. Each is driven by its own
spoke, which already proved itself in its own repo. The console does not
re-implement any of them; a driver locates the spoke and runs its proven entry
point, returning the sealed shard directory + the out-of-band public key.

This is the ONE place spoke coupling is allowed to live — contained in a driver,
never in the console core. Each surface declares its integration status
honestly: DRIVEN means the console runs it end to end here; DECLARED means the
adapter contract exists but the spoke drive is not wired in this build.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple


class Status(str, Enum):
    DRIVEN = "driven"       # console runs the spoke end to end, verified here
    DECLARED = "declared"   # adapter contract defined; spoke drive not wired yet


# A driver runs a surface and returns (shard_dir, trusted_key_path).
Driver = Callable[["SurfaceRun"], Tuple[Path, Path]]


@dataclass(frozen=True)
class SurfaceRun:
    """One request to capture/operate a surface. ``params`` are surface-specific
    (a fixture path, a sensor id, a dataset prefix). ``workdir`` is where the
    driver may stage and seal."""

    surface: str
    workdir: Path
    params: Dict[str, str]


@dataclass(frozen=True)
class Surface:
    name: str
    verb: str                 # "capture" or "operate"
    owner_repo: str
    tier: str
    status: Status
    summary: str
    driver: Optional[Driver] = None

    def run(self, run: SurfaceRun) -> Tuple[Path, Path]:
        if self.status is not Status.DRIVEN or self.driver is None:
            raise NotImplementedError(
                f"surface {self.name!r} is DECLARED, not driven in this build. Its spoke "
                f"({self.owner_repo}) proves it in its own repo; wiring the driver here is the "
                f"next step. The console core still verifies any shard {self.owner_repo} produces."
            )
        return self.driver(run)


# ---------------------------------------------------------------------------
# Driver: embodied frame capture (DRIVEN — pure-python spoke, sealed via genesis)
# ---------------------------------------------------------------------------

def _drive_frame_capture(run: SurfaceRun) -> Tuple[Path, Path]:
    """Drive axm-embodied frame capture to a sealed shard, in the spoke's repo
    context (so the console core never imports the spoke)."""
    import json
    import subprocess
    import sys
    import textwrap

    repo = Path(run.params.get("spoke_repo", os.environ.get("AXM_EMBODIED_REPO", "/workspace/axm-embodied")))
    if not (repo / "src" / "axm_embodied" / "frame_capture.py").exists():
        raise FileNotFoundError(
            f"axm-embodied spoke not found at {repo}. Set AXM_EMBODIED_REPO or pass spoke_repo."
        )
    out = run.workdir
    out.mkdir(parents=True, exist_ok=True)
    sensor = run.params.get("sensor_id", "doorcam-01")
    reason = run.params.get("reason", "motion")
    source = run.params.get("source", "pir-sensor-3")
    frames = int(run.params.get("frames", "40"))
    trigger_at = int(run.params.get("trigger_at", "18"))

    # Run the spoke's own recorder + compiler in its repo context. The console
    # hands over control entirely; it only collects the sealed shard afterward.
    script = textwrap.dedent(f"""
        import hashlib, json, sys
        from pathlib import Path
        from axm_build.sign import hybrid1_keygen
        from axm_embodied.frame_capture import FrameCaptureRecorder, FrameCaptureConfig
        from axm_embodied.frame_compile import compile_frame_capsule
        out = Path({str(out)!r})
        pub, key = hybrid1_keygen()
        cfg = FrameCaptureConfig(pre_window_frames=6, post_window_frames=6)
        with FrameCaptureRecorder(out, sensor_id={sensor!r}, config=cfg) as rec:
            for i in range({frames}):
                if i == {trigger_at}:
                    rec.trigger(reason={reason!r}, source={source!r})
                rec.observe_frame(hashlib.sha256(f"frame-{{i}}".encode()).digest()*32)
        cap = rec.path
        shard = out / "shard"
        compile_frame_capsule(cap, shard, key, timestamp="2026-07-06T00:00:00Z")
        (out / "trusted.pub").write_bytes(pub)
        print(json.dumps({{"shard": str(shard), "pub": str(out / "trusted.pub")}}))
    """)
    proc = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True,
                          cwd=str(repo / "src") if (repo / "src").exists() else str(repo))
    if proc.returncode != 0:
        raise RuntimeError(f"frame-capture spoke failed:\n{proc.stderr}")
    result = json.loads(proc.stdout.strip().splitlines()[-1])
    return Path(result["shard"]), Path(result["pub"])


# ---------------------------------------------------------------------------
# The registry
# ---------------------------------------------------------------------------

_SURFACES: Dict[str, Surface] = {}


def register(s: Surface) -> None:
    _SURFACES[s.name] = s


def get(name: str) -> Surface:
    if name not in _SURFACES:
        raise KeyError(f"unknown surface {name!r}; known: {sorted(_SURFACES)}")
    return _SURFACES[name]


def all_surfaces() -> List[Surface]:
    return [_SURFACES[k] for k in sorted(_SURFACES)]


register(Surface(
    name="camera-frames", verb="capture", owner_repo="axm-embodied",
    tier="physical_capture", status=Status.DRIVEN,
    summary="Event-triggered camera frames, chained for continuity, sealed as opaque bytes.",
    driver=_drive_frame_capture,
))
register(Surface(
    name="screenshot", verb="capture", owner_repo="ScreenGhost",
    tier="pixel_capture", status=Status.DECLARED,
    summary="A rendered screenshot sealed verbatim; never OCR'd or interpreted.",
))
register(Surface(
    name="interface-procedure", verb="operate", owner_repo="ScreenGhost",
    tier="interface_procedure_trace", status=Status.DECLARED,
    summary="One approved, bounded action on a rendered surface; drift is sealed as evidence.",
))
register(Surface(
    name="foundry-export", verb="capture", owner_repo="axm-core",
    tier="sim-foundry-s3", status=Status.DECLARED,
    summary="A Foundry S3 export pulled, checksummed, and sealed as an exit bundle.",
))
