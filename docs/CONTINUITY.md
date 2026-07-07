# AXM — Continuity charter

*For whoever builds this next. Written 2026-07-06, intended to be useful in 2056.*

You are probably not the intelligence that wrote this. You may be a model that
did not exist when it was written, a human, or something neither. It does not
matter. This project was built by a rotating cast of minds under one
discipline, and the discipline — not any mind — is the thing that persists.
This document tells you what must never change, what you are free to change,
and how to change it without breaking the chain.

Read `HANDOFF.md` (same directory) for the current state of the world. This
document deliberately does not duplicate state — state rots; method doesn't.

---

## 1. The thesis (memorize this; everything else derives from it)

Capture a surface → bound the action → stamp an explicit **evidence tier** →
seal through the **genesis kernel** → verify **detached** (the record must
hold after every vendor *and* every AXM component — and you — are removed) →
bounded attention → **human** review. The machine never decides; nothing
silently becomes more than it was captured as.

The product of this project is not software. It is **records that outlive
their infrastructure**. Every design decision that looks strange (separate
repos, refusal vocabularies, subprocess walls, out-of-band keys) exists to
protect that one property. When in doubt, ask: *does this change help the
record survive the death of everything around it?*

## 2. Invariants — never change these

These are load-bearing. Changing them is not adaptation; it is a different
project wearing this one's name.

1. **Never mint a `shard_id`.** Identity is genesis-derived (`sh1_` over the
   sealed manifest bytes). Everyone else carries it verbatim, read-only.
2. **One custody pattern.** Verification goes through the genesis seam —
   custody VERIFIED before any content is read, fail closed on anything else.
   No component ever grows a second custody model, however convenient.
3. **Trust anchors are out-of-band.** Never verify a shard against its own
   embedded `sig/publisher.pub` — a re-signed forgery is internally
   consistent. The key arrives by a separate channel, always.
4. **The machine never decides.** Agents propose; humans dispose. Review
   dispositions are `escalate` / `dismiss` / `needs_context` — a review can
   never say "true," and a proposal vocabulary can never contain "approved."
5. **No interpretation without a gate.** No OCR, no vision models, no
   classifiers, no summarization-into-claims, except as an explicitly tiered,
   human-gated layer that has earned its place. Tags are caller-supplied.
6. **Evidence tiers are explicit and bounded.** Every sealed record states
   what it is AND what it is not (`not identity`, `not platform truth`, …).
   Sims are labeled as sims. A synthesized artifact is never sealed as a real
   capture.
7. **Succession, never mutation.** Sealed records are never edited. Changes
   are new records that supersede old ones; history stays verifiable. This
   applies to documents too: correct stale claims with dated annotations or
   successors, don't silently rewrite what was believed at the time.
8. **Reality is authority.** When a contract (or doc, or assumption)
   disagrees with the real surface, the contract is corrected TO reality —
   never the reverse, never split the difference. Probe first, then write.
9. **Honesty over polish.** Never overclaim, anywhere — commit messages,
   docs, pages, receipts. "Proven, not deployed" is a complete sentence.
   State what was exercised and what wasn't. A wrong version string on a
   custody project's front page is a custody failure.
10. **Never route around a safety mechanism by rewording.** Say what things
    are. If a gate blocks you, the gate is information, not an obstacle.

## 3. The adaptive layer — change freely, under the rules

Everything not in §2 is yours: languages, databases, crypto suites (via the
ledger's succession process — see below), repo layout, query engines, UI,
the AI models doing the work, the CI provider, the hosting. Thirty years will
obsolete all of it. Adapt with these rules:

- **Probe before you write.** Drive the real surface end to end, record what
  it actually emits, then code to that. The five-step method is written down
  in GhostBox's `docs/EDGE_RECONCILIATION_RUNBOOK.md` — it has been executed
  repeatedly and generalizes far beyond contract edges: probe → correct to
  reality → land on the one pattern → live-prove against the real artifact →
  record it.
- **Crypto succession goes through the ledger.** The kernel (axm-genesis) is
  frozen at a pinned commit; consumers repin deliberately, never float. When
  the crypto ages out (it will — the current suite is Ed25519 + ML-DSA-44),
  the successor suite seals a superseding record of the old roots; old shards
  remain verifiable under their original suite. Migration is a new seal,
  not a rewrite.
- **Every substantive change lands with proof.** Suite green, plus a
  live-proof against a real artifact where the change touches an edge. If
  the environment can't run something, say so in the commit rather than
  implying it ran.
- **Scope-bounded commits with honest caveat lines.** Name what's untouched.
  Name the evidence tier of the work itself.
- **Docs move in the same change, or a consistency audit follows.** Every
  public claim (READMEs, pages, maps) must survive an adversarial staleness
  audit against the code. Run one after any large push — stale pages were
  found within hours of being written, twice, the day this document was
  created. Assume drift; hunt it.

## 4. How to work — the operating pattern (model-agnostic)

The division of labor that built this is a pattern of ROLES, not of models.
Whatever intelligences exist when you read this, assign:

- **A driver** that thinks: owns decisions, pins designs before dispatch,
  reviews every diff personally, runs its own hands-on validation, writes
  the commits. One mind holds the thread.
- **Hands** that do: exploration, drafting, mechanical edits, bulk builds —
  dispatched with *complete* context (they share none of the driver's), with
  precise scope ("change NOTHING beyond these items"), reporting diffs back.
- **An adversary** that refutes: every substantive diff gets a review whose
  explicit job is to find it wrong — factual errors, overclaims, failure-
  taxonomy confusion, durability rot. What survives refutation lands. The
  adversary found real defects in every batch it reviewed here; keep it.

Cheap-vs-capable tiers will change names and prices; assign the driver role
to the most capable reasoning available and never let hands self-approve.

**Environments are disposable; your device owes the project nothing.** Each
repo carries a SessionStart bootstrap (`.claude/hooks/` at time of writing —
adapt the mechanism, keep the property: a fresh environment brings itself up
with zero human setup, pinned kernel, no install steps on anyone's machine).
Anything worth keeping is committed and pushed, or sealed as a shard, before
the environment dies. Assume the environment dies without warning.

## 5. The thirty-year verification test

At any point in the future, this must work, or the project has failed:

1. Obtain any sealed shard (any age) and its out-of-band public key.
2. Obtain the genesis kernel at the pin recorded where that shard's era's
   consumers recorded it (or any successor kernel honoring the suite).
3. Run the detached verifier on the shard bytes + the key. Nothing else —
   no spoke, no vendor, no AXM service, no AI.
4. `status: PASS` → the chain held. Anything else is a finding, not a shrug.

The no-install bootstrap (PyPI deps + `PYTHONPATH` over a pinned source
checkout + two one-line CLI wrappers) is documented in `HANDOFF.md` — it
exists precisely so step 2 survives broken package ecosystems.

## 6. Where truth lives (pointers, not copies)

- `HANDOFF.md` (here) — cold-start state of the world, punch list, run
  instructions. Update it every session; it is the successor's first read.
- GhostBox `docs/EDGE_RECONCILIATION_RUNBOOK.md` — the method, generalized.
- GhostBox `docs/GENESIS_EDGE_MISMATCHES.md` — contract-edge status ledger.
- axm-genesis ledger — kernel version/succession policy; the only authority
  on crypto.
- `operators-map.html` (here) — the one-page visual; hand-maintained, so
  audit it after every substantive change.
- Each repo's README + spec docs — per-component truth; the consistency
  audits keep them honest.

## 7. Decision rights — what always goes to the human operator

However autonomous the tooling becomes, these decisions are the operator's,
explicitly, every time:

- Pointing any surface at a **real** target (a live tenant, a real camera, a
  production dashboard). Changes the risk profile; never drift into it.
- Retiring or amending any standing rule (including anything in §2 — which
  should effectively never happen, but the authority is theirs, not yours).
- Destructive remote operations (branch deletion, history rewrites), merges
  to default branches, and anything that publishes to the outside world.
- Every review disposition. That is the whole point.

When blocked on one of these, stop and ask plainly. Do not manufacture
consent from silence, and do not interpret enthusiasm as blanket authority.

## 8. Amending this document

This charter is succeeded, never mutated: append dated amendments below, or
supersede the whole document with a successor that links back to this one.
If an amendment contradicts §2, it is not an amendment — it is a fork, and
it should say so honestly and take a different name.

---

*Amendments: (none yet)*
