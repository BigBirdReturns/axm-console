# AXM — Handoff / state of the world

A cold-start brief for a fresh session. Everything below is on `main` across the
repos unless marked otherwise. The one-page visual is
[`operators-map.html`](operators-map.html).

## The thesis (don't lose this)

Capture a surface → bound the action → stamp an explicit **evidence tier** → seal
through **genesis** → verify **detached** (the record holds after every vendor
*and* every AXM component is removed) → bounded attention → **human** review. The
machine never decides; nothing silently becomes more than it was captured as.

Two standing rules: **simulate, don't wait** (no task stalls on live credentials;
sims are labeled as sims) and **no interpretation without a gate** (no OCR, no
vision models until a human-gated, tiered annotation layer earns it).

## Repositories (verdict: 6 real, 1 phantom)

| Repo | Role | Keep? |
|---|---|---|
| `axm-genesis` | frozen crypto kernel; seals `axm-hybrid1` shards, derives `sh1_`, verifies. **v1.0.0** @ `9074e7f` | **yes — the trust root** |
| `axm-core` | Palantir/Foundry exit + knowledge (sim S3 surface, exit bundle, graph loader) | yes |
| `ScreenGhost` | intake & operation (pixel_capture; interface procedures on real Chromium) | yes |
| `GhostBox` | attention & review (custody seam, observers, human review) | yes |
| `axm-embodied` | physical liability (Flash Freeze recorder; frame capture → physical_capture) | yes |
| `axm-console` | **the seat** — `axm capture/operate/verify/queue/review`, all 4 surfaces driven | yes |
| `axm-chat` | named in contracts, **empty, never built** | **build it or delete it — phantom** |

Separate repos are a deliberate cost: they make the sovereignty boundary a *hard
wall* (GhostBox can't import ScreenGhost as authority) instead of a lint rule.
Worth it for a custody project. A monorepo would cut coordination friction but
soften that wall — a real downgrade here.

## What's DONE (merged)

- All five spokes + the console, one custody chain, every record verifies detached.
- Console: all four surfaces **driven** (`camera-frames`, `screenshot`,
  `interface-procedure` on real Chromium, `foundry-export` on a sim S3 surface).
  CI drives `camera-frames` for real.
- Honesty pass done: synthesized screenshot labeled `synthesized_sample` (not a
  fake `manual_screenshot`); `KERNEL_ABSENT` receipt degrades instead of crashing;
  the operator map is durable and rebuilt from real state.
- Doctrine wins: retired the live-creds gate (Foundry S3 simulated at fidelity,
  which flushed out a real silent-truncation bug past 1000 objects).

## What's LEFT (the punch list)

1. **GhostBox ↔ embodied reconciliation** *(highest value — the last internal
   dishonesty).* GhostBox's `PhysicalEvidenceEvent` / `EmbodiedSource` in
   `GhostBox/src/ghostbox/interop/contracts.py` are **mirror-side guesses never
   checked against a real embodied shard.** Plan: drive a real `axm-embodied`
   frame-capture shard (or use `axm capture camera-frames`), run it against the
   declared contract, correct the contract *to reality* (the pattern used every
   time), and land a GhostBox physical-evidence observer — custody-verified first,
   bounded findings, mirroring `pixel_observer.py` / `knowledge_observer.py`.
2. **Package `axm-console`** — `pip install`, `axm` on PATH. Currently runs via
   `python -m axm_console.cli`. Small, high-leverage.
3. **`axm-chat`** — build the `ConversationShardRef` edge, or delete it from the
   map + `contracts.py`. Don't leave it a phantom.
4. **(Your call, retires a standing rule) point one surface at something real** —
   a real Foundry tenant, a real camera, a real vendor dashboard. Changes the risk
   profile; not to be drifted into. Every surface driver already resolves its
   spoke + target from params/env, so this is config, not new code.
5. **Cosmetic:** merged `claude/*` branches linger on several remotes (the git
   proxy refuses deletes; clear them in the GitHub UI).

## How to run things

```bash
# genesis kernel must be installed (v1.0.0 @ 9074e7f):
pip install 'git+https://github.com/BigBirdReturns/axm-genesis.git@9074e7fb2e9cedde692b248cdd0c6a805e77d8ac#egg=axm-genesis[mldsa-compat]'

# console: core tests need only the kernel; driver tests need the spokes checked out
cd axm-console && python -m pytest tests/ -q      # 10 core pass; 5 driver tests skip w/o spokes
AXM_EMBODIED_REPO=/path/to/axm-embodied \
AXM_SCREENGHOST_REPO=/path/to/screenghost \
AXM_CORE_REPO=/path/to/axm-core python -m pytest tests/ -q   # all 17

# drive a surface end to end:
axm surfaces
axm capture camera-frames
axm queue
axm review <sh1_id> --by you --as escalate
```

## Boundaries a new session must not cross

- Never mint a `shard_id` — it's genesis-derived, read-only to everyone else.
- Never let a review say "true" — dispositions are `escalate` / `dismiss` /
  `needs_context` only.
- Never seal a synthesized/placeholder artifact as a real capture.
- Never add OCR / vision / a classifier except as a tiered, human-gated layer.
- Never route around a safety mechanism by rewording — say what things are.

## Caveats (evidence tier of the whole thing)

Proven, not deployed. Crypto is the pure-Python `dilithium-py` fallback
(functional, not load-proven). All surfaces are sims or local fixtures. Nothing
has crossed a real vendor, tenant, camera, or dashboard yet — by rule, until you
choose to.
