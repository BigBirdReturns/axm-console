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
axm ask <shard_dir> --key <pub> "what links to Aircraft"   # verify-gated query, SQL or NL
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
| `camera-frames` | capture | `physical_capture` | axm-embodied | **driven** |
| `screenshot` | capture | `pixel_capture` | ScreenGhost | **driven** |
| `interface-procedure` | operate | `interface_procedure_trace` | ScreenGhost | **driven** |
| `foundry-export` | capture | `sim-foundry-s3` | axm-core | **driven** |
| `ontology-exit` | capture | `foundry-ontology-wire-shape-reconciled` | axm-core | **driven** |

All five surfaces are **driven** — the console runs each spoke end to end and
verifies the sealed result here. A driver runs the spoke's own proven entry point
in the spoke's repo context (a subprocess), so the console core never imports a
spoke; the coupling is confined to the driver. Spoke locations resolve from
`AXM_EMBODIED_REPO` / `AXM_SCREENGHOST_REPO` / `AXM_CORE_REPO` (with deployment
defaults), or a per-run `spoke_repo` param.

The refusal contract still stands: any future **declared** surface raises rather
than faking a run — no Potemkin capture.

> Note: the `foundry-export` bundle does not embed an `evidence_tier` in its
> manifest, so the console honestly reports its tier as *unstated by the shard*
> rather than inventing one. The record still verifies detached like the rest.

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

## Map

[`index.html`](index.html) is a single-page, self-
contained map of the whole ecosystem — every repository, the shared pattern, the
tier vocabulary, the four flows, and (honestly) where "proven" stops and "not yet
deployed" begins. Open it directly or serve it via Pages.

## Status

v0. Core (verify-detached → receipt → queue) proven against genesis **v1.0.0**;
**all five surfaces driven end to end** — camera-frames, screenshot,
interface-procedure (real Chromium), foundry-export (simulated S3), and
ontology-exit (Foundry Ontology API v2 wire shapes). The spoke-independent core
suite runs everywhere; **CI now also checks out a spoke and drives
`camera-frames` for real**, so the cross-repo claim is covered, not just proven
off-CI. The remaining driver integration tests run wherever their spokes are
checked out and skip cleanly otherwise. `axm ask` is the seat's first READ verb
— verify-gated SQL/NL querying of any sealed shard through Spectra.

Honesty fixes on this pass: a no-argument `screenshot` seals a labeled
`synthesized_sample`, never a fake `manual_screenshot`; a kernel-absent receipt
degrades gracefully instead of crashing.
