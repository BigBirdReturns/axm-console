# AXM Operator Console

**One seat over the AXM sovereign evidence ecosystem.** The spokes (axm-core,
ScreenGhost, GhostBox, axm-embodied) each prove a surface in their own repo. This
is the cockpit that lets *you* drive them: pick a surface, get back a
genesis-sealed record that verifies **detached**, a plain-English receipt, and a
review queue that's yours.

```
pick a surface → drive its spoke to a sealed shard → verify DETACHED
   → plain-English receipt → admit to your review queue → your decision
```

## The console owns nothing

That is the whole point. Sealing stays in the spokes (through the genesis
kernel); verification is the kernel's; the review queue records human decisions
and makes none. The console core depends only on **axm-genesis** — the one
legitimate shared root. Each surface driver is a contained adapter over a spoke's
already-proven code; that coupling lives in the driver, never in the core.

## Use it

```bash
axm surfaces                        # what you can capture or operate
axm capture camera-frames           # drive a surface → sealed, verified record
axm verify <shard_dir> --key <pub>  # verify ANY sealed shard, from any spoke
axm queue                           # your review queue
axm review <shard_id> --by you --as escalate --note "look at this"
```

A real run, this environment:

```
AXM CUSTODY RECEIPT
────────────────────────────────────────────────────────────
  record    Frame capture capsule capture-c1dc5e2b
  tier      physical_capture
              · opaque sensor bytes within declared trigger windows only
              · not identity
              · not activity or semantic classification
              · not continuous coverage (gaps between windows are declared, not hidden)
              · not platform truth
              · not legal-grade provenance by itself
  shard id  sh1_79eb5e944a1656577990621a3f428ca79658ce49bdfea2eee9ad5dd0f382affa
  suite     axm-hybrid1
  verify    PASS ✓
  proven    verifiable with only these bytes + the out-of-band key,
            after all of the following are removed:
              — the originating spoke  — the vendor / platform
              — the browser or sensor  — any AI layer
────────────────────────────────────────────────────────────
```

## Surfaces

| Surface | Verb | Tier | Owner | Status |
|---|---|---|---|---|
| `camera-frames` | capture | `physical_capture` | axm-embodied | **driven** — run end to end here |
| `screenshot` | capture | `pixel_capture` | ScreenGhost | declared |
| `interface-procedure` | operate | `interface_procedure_trace` | ScreenGhost | declared |
| `foundry-export` | capture | `sim-foundry-s3` | axm-core | declared |

**driven** = the console runs the spoke end to end and verifies the result here.
**declared** = the adapter contract exists and the spoke proves the surface in its
own repo; wiring the driver into the console is the next step. A declared surface
**refuses** rather than faking a run — no Potemkin capture. The core still
verifies any shard those spokes produce, today, via `axm verify`.

## Discipline (inherited, enforced, tested)

- **Verified or nothing.** A record that does not verify detached is refused from
  the queue.
- **Attention-only review.** Dispositions are `escalate` / `dismiss` /
  `needs_context`. There is no `authentic`, no `true` — a review moves attention,
  it never adjudicates the record or upgrades its tier.
- **Human-attributed, append-only.** Every decision names a human; history is a
  plain JSONL ledger that nothing overwrites.
- **The console never mints custody.** `shard_id` is genesis-derived; the console
  reads it, never assigns it.

## Status

v0. Core (verify-detached → receipt → queue) proven against genesis **v1.0.0**;
the `camera-frames` surface driven end to end; 10/10 tests. Remaining surface
drivers are declared adapters — the honest next increment, each a thin wrapper
over a spoke that already passes its own suite.
