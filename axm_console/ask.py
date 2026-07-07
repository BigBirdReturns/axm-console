"""axm ask — the console's first READ verb.

Every other console capability writes a new sealed record; ``ask`` reads one
that already exists. It mounts a sealed shard into axm-core's Spectra query
engine (axiom_runtime) and runs a query against it — either raw SQL or a
free-text question translated by Spectra's own NL layer.

Verify-gated, always: the engine's own custody gate (the same real genesis
``axm-verify`` the rest of the console depends on) runs the detached
verification against the out-of-band key BEFORE any content is queryable. The
console never pre-reads shard content and never queries a shard it cannot
verify — an operator without a trusted key gets refused, not a guess.

Spoke coupling is confined to a subprocess run in the spoke's own repo
context, exactly like a surface driver (see ``surfaces.py``): the console
core never imports axiom_runtime.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Dict, List, Optional


class AskError(RuntimeError):
    pass


def resolve_core_repo(spoke_repo: Optional[str] = None) -> Path:
    return Path(spoke_repo or os.environ.get("AXM_CORE_REPO", "/workspace/axm-core"))


def ask(
    shard_dir: str | Path,
    trusted_key: str | Path,
    *,
    sql: Optional[str] = None,
    question: Optional[str] = None,
    spoke_repo: Optional[str] = None,
) -> Dict[str, object]:
    """Mount ``shard_dir`` through axm-core's Spectra engine and query it.

    Exactly one of ``sql`` / ``question`` should be given; ``sql`` wins if
    both are. Returns ``{"shard_id", "columns", "rows"}`` — never the shard's
    content directly, only what the query engine (behind the verify gate)
    answers.
    """
    repo = resolve_core_repo(spoke_repo)
    if not (repo / "spectra" / "axiom_runtime" / "engine.py").exists():
        raise AskError(
            f"axm-core spoke not found at {repo} (set AXM_CORE_REPO). "
            f"`axm ask` needs the axm-core checkout for its Spectra engine."
        )
    script = f"""
        import json, os, sys, tempfile
        from pathlib import Path
        sys.path.insert(0, str(Path({str(repo)!r}) / "spectra"))
        os.environ["SPECTRA_DEV_MODE"] = "1"
        os.environ["SPECTRA_TRUSTED_PUBKEY"] = {str(trusted_key)!r}
        from axiom_runtime.engine import SpectraEngine
        work = Path(tempfile.mkdtemp(prefix="axm_ask_"))
        eng = SpectraEngine(db_path=str(work / "spectra.db"),
                            audit_path=str(work / "audit.jsonl"),
                            cache_path=str(work / "cache.jsonl"))
        # The engine's own custody gate verifies detached against the
        # out-of-band SPECTRA_TRUSTED_PUBKEY before anything is queryable.
        spec = eng.mount_shard({str(shard_dir)!r})
        sql = {sql!r}
        question = {question!r}
        if sql:
            query_sql, params = sql, None
        else:
            from axiom_runtime.nlquery import natural_language_to_query
            query_sql, params = natural_language_to_query(question)
        result = eng.query_json(query_sql, params)
        print(json.dumps({{"shard_id": spec.shard_id, "columns": result["columns"],
                            "rows": result["rows"]}}))
    """
    proc = subprocess.run([sys.executable, "-c", textwrap.dedent(script)],
                          capture_output=True, text=True, cwd=str(repo))
    if proc.returncode != 0:
        err = proc.stderr.strip()
        # Failure classes are kept distinct on purpose: a custody refusal must
        # never read as an environment problem (or vice versa).
        if any(sig in err for sig in ("E_SIG_INVALID", "'status': 'FAIL'", '"status": "FAIL"',
                                      "Cannot read trusted key", "MALFORMED")):
            raise AskError(f"custody verification failed — the engine refused to mount "
                           f"the shard (check --key is the right out-of-band anchor):\n"
                           f"{err[-400:]}")
        if "ModuleNotFoundError" in err:
            raise AskError(f"axm-core Spectra engine not importable from {repo}\n{err[-400:]}")
        raise AskError(f"query failed:\n{err[-800:]}")
    return json.loads(proc.stdout.strip().splitlines()[-1])


def render_table(columns: List[str], rows: List[list], shard_id: str) -> str:
    """Plain rows + a one-line provenance footer — no framing beyond that."""
    if not rows:
        body = "no rows."
    else:
        widths = [max(len(str(c)), max((len(str(r[i])) for r in rows), default=0))
                  for i, c in enumerate(columns)]
        header = "  ".join(str(c).ljust(w) for c, w in zip(columns, widths))
        sep = "  ".join("-" * w for w in widths)
        lines = [header, sep]
        for row in rows:
            lines.append("  ".join(str(v).ljust(w) for v, w in zip(row, widths)))
        body = "\n".join(lines)
    footer = f"{shard_id}  verified via Spectra custody gate"
    return f"{body}\n\n{footer}"
