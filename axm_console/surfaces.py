"""Surface registry — the assembly layer.

A *surface* is anything the operator can capture or operate: a Foundry export, a
screenshot, a dashboard procedure, a camera trigger. Each is driven by its own
spoke, which already proved itself in its own repo. The console does not
re-implement any of them; a driver locates the spoke, runs its proven entry
point IN THE SPOKE'S OWN REPO CONTEXT (a subprocess), and returns the sealed
shard directory + the out-of-band public key.

This is the ONE place spoke coupling lives — inside a driver, as a subprocess,
never in the console core's import graph. Each surface declares its integration
status honestly: DRIVEN means the console runs it end to end; DECLARED means the
adapter contract exists but the spoke drive is not wired.

Spoke locations resolve from the environment (with deployment-shaped defaults)
so the same drivers work wherever an operator has the spokes checked out:
    AXM_EMBODIED_REPO   AXM_SCREENGHOST_REPO   GHOSTBOX_REPO
A per-run ``spoke_repo`` param overrides the default for that run.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple


class Status(str, Enum):
    DRIVEN = "driven"       # console runs the spoke end to end, verified here
    DECLARED = "declared"   # adapter contract defined; spoke drive not wired yet


Driver = Callable[["SurfaceRun"], Tuple[Path, Path]]


@dataclass(frozen=True)
class SurfaceRun:
    surface: str
    workdir: Path
    params: Dict[str, str]


@dataclass(frozen=True)
class Surface:
    name: str
    verb: str
    owner_repo: str
    tier: str
    status: Status
    summary: str
    driver: Optional[Driver] = None

    def run(self, run: SurfaceRun) -> Tuple[Path, Path]:
        if self.status is not Status.DRIVEN or self.driver is None:
            raise NotImplementedError(
                f"surface {self.name!r} is DECLARED, not driven in this build. Its spoke "
                f"({self.owner_repo}) proves it in its own repo; the console core still "
                f"verifies any shard it produces via `axm verify`."
            )
        return self.driver(run)


def _resolve_repo(run: SurfaceRun, env_var: str, default: str) -> Path:
    return Path(run.params.get("spoke_repo") or os.environ.get(env_var, default))


def _run_in_spoke(cwd: Path, script: str, missing_hint: str) -> Tuple[Path, Path]:
    """Run a spoke script in its repo context; return (shard_dir, pub_key).

    The script must print a final JSON line: {"shard": <dir>, "pub": <pubkey>}.
    Any earlier stdout lines are forwarded verbatim to the operator (e.g. an
    honesty note that a default/synthesized input was used) before the JSON
    line is parsed. Spoke coupling is confined to this subprocess; the console
    core never imports a spoke.
    """
    proc = subprocess.run([sys.executable, "-c", textwrap.dedent(script)],
                          capture_output=True, text=True, cwd=str(cwd))
    if proc.returncode != 0:
        if "ModuleNotFoundError" in proc.stderr or "No such file" in proc.stderr:
            raise FileNotFoundError(f"{missing_hint}\n{proc.stderr.strip()[-400:]}")
        raise RuntimeError(f"spoke run failed:\n{proc.stderr.strip()[-800:]}")
    lines = proc.stdout.strip().splitlines()
    for line in lines[:-1]:
        print(line)
    result = json.loads(lines[-1])
    return Path(result["shard"]), Path(result["pub"])


# ---------------------------------------------------------------------------
# camera-frames  (axm-embodied)
# ---------------------------------------------------------------------------

def _drive_camera_frames(run: SurfaceRun) -> Tuple[Path, Path]:
    repo = _resolve_repo(run, "AXM_EMBODIED_REPO", "/workspace/axm-embodied")
    src = repo / "src"
    if not (src / "axm_embodied" / "frame_capture.py").exists():
        raise FileNotFoundError(f"axm-embodied spoke not found at {repo} (set AXM_EMBODIED_REPO).")
    out = run.workdir
    out.mkdir(parents=True, exist_ok=True)
    p = run.params
    script = f"""
        import hashlib, json
        from pathlib import Path
        from axm_build.sign import hybrid1_keygen
        from axm_embodied.frame_capture import FrameCaptureRecorder, FrameCaptureConfig
        from axm_embodied.frame_compile import compile_frame_capsule
        out = Path({str(out)!r})
        pub, key = hybrid1_keygen()
        cfg = FrameCaptureConfig(pre_window_frames=6, post_window_frames=6)
        with FrameCaptureRecorder(out, sensor_id={p.get("sensor_id", "doorcam-01")!r}, config=cfg) as rec:
            for i in range({int(p.get("frames", "40"))}):
                if i == {int(p.get("trigger_at", "18"))}:
                    rec.trigger(reason={p.get("reason", "motion")!r}, source={p.get("source", "pir-sensor-3")!r})
                rec.observe_frame(hashlib.sha256(f"frame-{{i}}".encode()).digest()*32)
        shard = out / "shard"
        compile_frame_capsule(rec.path, shard, key, timestamp="2026-07-06T00:00:00Z")
        (out / "trusted.pub").write_bytes(pub)
        print(json.dumps({{"shard": str(shard), "pub": str(out / "trusted.pub")}}))
    """
    return _run_in_spoke(src, script, f"axm-embodied not importable from {src}")


# ---------------------------------------------------------------------------
# screenshot  (ScreenGhost — pixel_capture)
# ---------------------------------------------------------------------------

def _drive_screenshot(run: SurfaceRun) -> Tuple[Path, Path]:
    repo = _resolve_repo(run, "AXM_SCREENGHOST_REPO", "/workspace/screenghost")
    if not (repo / "core" / "pixel_seal.py").exists():
        raise FileNotFoundError(f"ScreenGhost spoke not found at {repo} (set AXM_SCREENGHOST_REPO).")
    out = run.workdir
    out.mkdir(parents=True, exist_ok=True)
    p = run.params
    png_path = p.get("png_path", "")
    sidecar = {k: p[k] for k in ("url", "page_title", "app_name", "capture_tool") if p.get(k)}
    # Honesty: a synthesized placeholder must NEVER be sealed as a real capture.
    # With no png_path we seal a labeled sample; only a real png_path is a real
    # capture that may carry the operator's capture_method/source_label.
    if png_path:
        capture_method = p.get("capture_method", "manual_screenshot")
        source_label = p.get("source_label", "operator-console")
    else:
        capture_method = "synthesized_sample"
        source_label = "operator-console (synthesized sample, not a real capture)"
    script = f"""
        import json, struct, zlib
        from pathlib import Path
        from core.pixel_evidence import build_capture
        from core.pixel_seal import seal_pixel_evidence
        out = Path({str(out)!r})
        png_path = {png_path!r}
        if png_path:
            png = Path(png_path).read_bytes()
        else:
            sig = b"\\x89PNG\\r\\n\\x1a\\n"
            def chunk(t, d):
                c = t + d
                return struct.pack(">I", len(d)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
            ihdr = struct.pack(">IIBBBBB", 6, 4, 8, 2, 0, 0, 0)
            raw = b"".join(b"\\x00" + b"\\x22\\x44\\x66"*6 for _ in range(4))
            png = sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
        capture = build_capture(png, capture_method={capture_method!r},
                                source_label={source_label!r},
                                sidecar={sidecar!r} or None)
        shard = out / "shard"
        sealed = seal_pixel_evidence(png, capture, shard, work_dir=out)
        print(json.dumps({{"shard": sealed.shard_dir, "pub": sealed.trusted_key_path}}))
    """
    return _run_in_spoke(repo, script, f"ScreenGhost core not importable from {repo}")


# ---------------------------------------------------------------------------
# interface-procedure  (ScreenGhost — real Chromium, sealed trace)
# ---------------------------------------------------------------------------

def _drive_interface_procedure(run: SurfaceRun) -> Tuple[Path, Path]:
    repo = _resolve_repo(run, "AXM_SCREENGHOST_REPO", "/workspace/screenghost")
    if not (repo / "core" / "procedure_seal.py").exists():
        raise FileNotFoundError(f"ScreenGhost spoke not found at {repo} (set AXM_SCREENGHOST_REPO).")
    out = run.workdir
    out.mkdir(parents=True, exist_ok=True)
    p = run.params
    fixture = p.get("fixture", str(repo / "examples" / "fixtures" / "interface_surface" / "dashboard.html"))
    chromium = p.get("chromium", os.environ.get("SCREENGHOST_CHROMIUM", "/opt/pw-browsers/chromium"))
    script = f"""
        import json
        from pathlib import Path
        from core.interface_procedure import (InterfaceProcedure, ApprovedBounds,
            ProcedureRunner, PlaywrightSurfaceDriver)
        from core.procedure_seal import seal_trace
        out = Path({str(out)!r})
        exe = {chromium!r}
        exe = exe if Path(exe).exists() else None
        proc = InterfaceProcedure(
            procedure_id={p.get("procedure_id", "proc-lamp-on-v0")!r},
            surface_label={p.get("surface_label", "local-fixture-surface")!r},
            anchor_selector="#dashboard-title", anchor_text="Home Dashboard",
            target_selector="#tile-living-room-lamp", target_label="Living Room Lamp",
            approved_bounds=ApprovedBounds(x=20, y=100, width=300, height=160),
            verify_selector="#lamp-state", verify_expected_text="On", verify_timeout_ms=1500)
        driver = PlaywrightSurfaceDriver(Path({fixture!r}).as_uri(), executable_path=exe)
        try:
            trace = ProcedureRunner().run(driver, proc)
        finally:
            driver.close()
        shard = out / "shard"
        sealed = seal_trace(trace, shard, work_dir=out)
        print(json.dumps({{"shard": sealed.shard_dir, "pub": sealed.trusted_key_path}}))
    """
    return _run_in_spoke(repo, script, f"ScreenGhost core / playwright not available at {repo}")


# ---------------------------------------------------------------------------
# foundry-export  (axm-core — sim S3 surface, fully offline)
# ---------------------------------------------------------------------------

def _drive_foundry_export(run: SurfaceRun) -> Tuple[Path, Path]:
    repo = _resolve_repo(run, "GHOSTBOX_REPO", "/workspace/GhostBox")
    if not (repo / "foundry_exit" / "sim_surface.py").exists():
        raise FileNotFoundError(f"GhostBox spoke (foundry_exit) not found at {repo} (set GHOSTBOX_REPO).")
    out = run.workdir
    out.mkdir(parents=True, exist_ok=True)
    p = run.params
    n = int(p.get("objects", "200"))
    scope = p.get("prefix", "datasets/orders/")
    rid = p.get("dataset_rid", "ri.foundry.main.dataset.orders")
    script = f"""
        import json
        from pathlib import Path
        from foundry_exit.sim_surface import FoundryS3Sim
        from foundry_exit.adapters import S3Config, S3ExportSource
        from foundry_exit.importer import FoundryExitImporter
        from foundry_exit.bundle import build_bundle
        from foundry_exit.seal import seal_exit_bundle
        from foundry_exit.live_probe import build_inventory_from_listing
        out = Path({str(out)!r})
        BUCKET, SCOPE, RID = "foundry-export-sim", {scope!r}, {rid!r}
        sim = FoundryS3Sim(bucket=BUCKET, page_size=64)
        for i in range({n}):
            sim.put(f"{{SCOPE}}part-{{i:04d}}.csv", f"order,{{i}}\\n".encode())
        src = S3ExportSource(S3Config(endpoint_url="sim://", bucket=BUCKET, prefix=""), client=sim)
        inv = build_inventory_from_listing(src, dataset_rid=RID, prefix=SCOPE)
        manifest = FoundryExitImporter(src, stage_dir=out / "staged").import_export(
            inventory=inv, ontology={{"object_types": [{{"object_type_id": "Order"}}]}}, lineage={{"edges": []}})
        bundle = build_bundle(manifest, out / "bundle")
        sealed = seal_exit_bundle(manifest, bundle, out / "shard")
        print(json.dumps({{"shard": sealed.shard_dir, "pub": sealed.trusted_key_path}}))
    """
    return _run_in_spoke(repo, script, f"GhostBox foundry_exit not importable from {repo}")


# ---------------------------------------------------------------------------
# ontology-exit  (axm-core — Foundry Ontology API v2 capture, fully offline)
# ---------------------------------------------------------------------------

def _drive_ontology_exit(run: SurfaceRun) -> Tuple[Path, Path]:
    repo = _resolve_repo(run, "GHOSTBOX_REPO", "/workspace/GhostBox")
    if not (repo / "foundry_exit" / "ontology_api.py").exists():
        raise FileNotFoundError(f"GhostBox spoke (foundry_exit) not found at {repo} (set GHOSTBOX_REPO).")
    out = run.workdir
    out.mkdir(parents=True, exist_ok=True)
    p = run.params
    capture = p.get("capture")
    script = f"""
        import json
        from pathlib import Path
        from foundry_exit.ontology_api import load_ontology_capture
        from foundry_exit.ontology_seal import seal_ontology_capture
        out = Path({str(out)!r})
        repo = Path({str(repo)!r})
        capture_arg = {capture!r}
        if capture_arg:
            capture_dir = Path(capture_arg)
        else:
            capture_dir = repo / "samples" / "foundry_ontology_fixture"
            print("note: no capture= param given; sealing the repo's bundled sample "
                  "(samples/foundry_ontology_fixture) -- an INVENTED sample in the "
                  "documented Ontology API v2 wire shape, NOT a live tenant capture.")
        capture = load_ontology_capture(capture_dir)
        shard = out / "shard"
        sealed = seal_ontology_capture(capture, shard)
        print(json.dumps({{"shard": sealed.shard_dir, "pub": sealed.trusted_key_path}}))
    """
    return _run_in_spoke(repo, script, f"GhostBox foundry_exit ontology_api not importable from {repo}")


# ---------------------------------------------------------------------------
# registry
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
    driver=_drive_camera_frames,
))
register(Surface(
    name="screenshot", verb="capture", owner_repo="ScreenGhost",
    tier="pixel_capture", status=Status.DRIVEN,
    summary="A rendered screenshot sealed verbatim; never OCR'd or interpreted.",
    driver=_drive_screenshot,
))
register(Surface(
    name="interface-procedure", verb="operate", owner_repo="ScreenGhost",
    tier="interface_procedure_trace", status=Status.DRIVEN,
    summary="One approved, bounded action on a real rendered surface; drift is sealed as evidence.",
    driver=_drive_interface_procedure,
))
register(Surface(
    name="foundry-export", verb="capture", owner_repo="axm-core",
    tier="sim-foundry-s3", status=Status.DRIVEN,
    summary="A Foundry S3 export (simulated surface) pulled, checksummed, and sealed as an exit bundle.",
    driver=_drive_foundry_export,
))
register(Surface(
    name="ontology-exit", verb="capture", owner_repo="axm-core",
    tier="foundry-ontology-wire-shape-reconciled", status=Status.DRIVEN,
    summary="A Foundry Ontology API v2 capture (objectTypes/linkTypes/objects JSON) sealed as a queryable exit shard.",
    driver=_drive_ontology_exit,
))
