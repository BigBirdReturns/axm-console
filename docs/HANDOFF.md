# AXM — Handoff / state of the world

A cold-start brief for a fresh session. Everything below is on `main` across the
repos unless marked otherwise. The one-page visual is
[`operators-map.html`](operators-map.html). **If you are new to this project —
any model, any decade — read [`CONTINUITY.md`](CONTINUITY.md) first:** it
separates what must never change from what you are free to change, and how.

## The thesis (don't lose this)

Capture a surface → bound the action → stamp an explicit **evidence tier** → seal
through **genesis** → verify **detached** (the record holds after every vendor
*and* every AXM component is removed) → bounded attention → **human** review. The
machine never decides; nothing silently becomes more than it was captured as.

Two standing rules: **simulate, don't wait** (no task stalls on live credentials;
sims are labeled as sims) and **no interpretation without a gate** (no OCR, no
vision models until a human-gated, tiered annotation layer earns it).

## Repositories (verdict: 7 real, 0 phantom)

*(Correction, 2026-07-06: the earlier "axm-chat is an empty phantom" verdict
was stale — the repo was already fully built (spoke, distiller, CLI, tests,
ingester, reconciled onto the v1 kernel per RFC 0007). What was actually
phantom was the GhostBox **edge**: `ConversationShardRef` was a mirror-side
guess never checked against a real axm-chat shard. That edge is now wired —
see the punch list.)*

| Repo | Role | Keep? |
|---|---|---|
| `axm-genesis` | frozen crypto kernel; seals `axm-hybrid1` shards, derives `sh1_`, verifies. **v1.0.0** @ `9074e7f` | **yes — the trust root** |
| `axm-core` | Palantir/Foundry exit + knowledge (sim S3 surface, exit bundle, graph loader) | yes |
| `ScreenGhost` | intake & operation (pixel_capture; interface procedures on real Chromium) | yes |
| `GhostBox` | attention & review (custody seam, observers, human review) | yes |
| `axm-embodied` | physical liability (Flash Freeze recorder; frame capture → physical_capture) | yes |
| `axm-console` | **the seat** — `axm capture/operate/verify/queue/review/ask`, all 5 surfaces driven | yes |
| `axm-chat` | conversation spoke (`import` → sealed `chat/conversation` shards); GhostBox edge wired | yes |

Separate repos are a deliberate cost: they make the sovereignty boundary a *hard
wall* (GhostBox can't import ScreenGhost as authority) instead of a lint rule.
Worth it for a custody project. A monorepo would cut coordination friction but
soften that wall — a real downgrade here.

## What's DONE (merged)

- All five spokes + the console, one custody chain, every record verifies detached.
- Console: all five surfaces **driven** (`camera-frames`, `screenshot`,
  `interface-procedure` on real Chromium, `foundry-export` on a sim S3 surface,
  `ontology-exit` on Foundry Ontology API v2 wire shapes). CI drives
  `camera-frames` for real. `axm ask` is the seat's first READ verb —
  verify-gated querying (SQL or NL) of any sealed shard through Spectra.
- Honesty pass done: synthesized screenshot labeled `synthesized_sample` (not a
  fake `manual_screenshot`); `KERNEL_ABSENT` receipt degrades instead of crashing;
  the operator map is durable and rebuilt from real state.
- Doctrine wins: retired the live-creds gate (Foundry S3 simulated at fidelity,
  which flushed out a real silent-truncation bug past 1000 objects).

## What's LEFT (the punch list)

*(Updated 2026-07-06 — session on `claude/session-planning-1h0xlw`.)*

1. ~~**GhostBox ↔ embodied reconciliation**~~ **DONE.** A real
   `FrameCaptureRecorder` session (sim frames, labeled as sim) was driven and
   sealed via the real `compile_frame_capsule`, verified detached. Contract
   corrected to reality (`fidelity` removed, `trigger_source` + `frame_id`
   added, `EmbodiedSource` annotated as an adapter role);
   `physical_observer.py` landed on the one custody pattern, live-proven
   against the real probe shard. GhostBox suite 108/108.
2. ~~**Package `axm-console`**~~ **was already done** — `pyproject.toml` has
   carried `[project.scripts] axm = "axm_console.cli:main"` all along; the
   entry point was verified working this session (invoked exactly as pip wires
   it, plus the full suite 17/17 with the kernel + playwright present). The
   earlier "runs via `python -m` only" note was stale.
3. ~~**`axm-chat`**~~ **DONE** (the repo was never the phantom — the edge was).
   A real `axm-chat import` was probed; `ConversationShardRef` now composes
   over `SealedShard` (same reconciliation as the axm-core edge), and
   `conversation_observer.py` landed on the one custody pattern, live-proven
   against the real probe shard. One reality correction: axm-chat exports NO
   shard-reference API, so `ConversationSpoke` is documented as a
   consumer-side adapter role.
4. **(Your call, retires a standing rule) point one surface at something real** —
   a real Foundry tenant, a real camera, a real vendor dashboard. Changes the risk
   profile; not to be drifted into. Every surface driver already resolves its
   spoke + target from params/env, so this is config, not new code.
5. **Cosmetic:** merged `claude/*` branches linger on several remotes.
   *(Corrected 2026-07-06: the earlier "git proxy refuses deletes" claim was
   never tested — the actual blocker is the session permission layer, which
   requires the operator to explicitly authorize remote branch deletion. On
   GhostBox, five branches are verified safe to delete via merged-PR state
   (#2–#6): `screenghost-ghostbox-prs-vve6um`, `axm-sovereign-spine-v0`,
   `axm-core-knowledge-edge`, `ghostbox-pixel-evidence-observer-v0`,
   `ghostbox-pixel-review-v0`. `threat-geometry-paper-vdbnp0` is PR #1 — a
   deliberate open reconcile-or-close decision, do NOT delete. Other repos:
   run the same merged-PR check before deleting; branch-tip ancestry is
   useless here because PRs are squash-merged.)*

6. ~~**axm-aide v0 adversarial review**~~ **CLOSED** (`axm-aide` @ `6ea94b1`).
   The refutation pass ran after the limit reset: doctrine and custody held
   under attack (proposal smuggling, self-disposition, tag inference, and
   pre-verify reads all structurally refuted). Two real correctness findings
   fixed and pinned by regression tests — same-second status resolution was
   decided by shard-name (i.e. status-word) sort order, now broken by a
   per-task `status_seq` claim in both resolution paths; and colliding
   caller content now refuses cleanly instead of surfacing a kernel
   traceback. Brief refuses loudly over a fully-unverifiable store; the v0
   one-key-pool trust limit is stated in LOOP.md. Suite 31/31.

With 1–3 closed, **every GhostBox interop edge has now been reconciled against
its real surface** (`docs/GENESIS_EDGE_MISMATCHES.md` in GhostBox tracks the
full status). The remaining items are a deliberate risk decision (4), UI
housekeeping (5), and one open review debt (6).

## How to run things

```bash
# genesis kernel must be installed (v1.0.0 @ 9074e7f):
pip install 'git+https://github.com/BigBirdReturns/axm-genesis.git@9074e7fb2e9cedde692b248cdd0c6a805e77d8ac#egg=axm-genesis[mldsa-compat]'

# no-install fallback (sandboxes where pip-from-git is blocked): check out
# axm-genesis at the SAME pinned commit and run it from source —
#   pip install blake3 pynacl click 'dilithium-py>=0.5.0'   # PyPI deps only
#   export PYTHONPATH=/path/to/axm-genesis/src
# plus thin axm-build / axm-verify wrappers on PATH, each one line of shell:
#   exec python3 -c "from axm_build.cli import main; main()" "$@"     # axm-build
#   exec python3 -c "from axm_verify.cli import main; main()" "$@"    # axm-verify
# (wrappers must export the PYTHONPATH above; the whole 108-test GhostBox
#  suite and the 17-test console suite run this way — verified 2026-07-06)

# console: core tests need only the kernel; driver tests need the spokes checked out
cd axm-console && python -m pytest tests/ -q      # 12 core pass; 8 driver/ask tests skip w/o spokes
AXM_EMBODIED_REPO=/path/to/axm-embodied \
AXM_SCREENGHOST_REPO=/path/to/screenghost \
AXM_CORE_REPO=/path/to/axm-core python -m pytest tests/ -q   # all 20

# drive a surface end to end:
axm surfaces
axm capture camera-frames
axm capture ontology-exit
axm ask <shard_dir> --key <pub> --sql "SELECT DISTINCT label FROM entities WHERE entity_type = 'object_type'"
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
