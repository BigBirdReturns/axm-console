"""`axm ask` — the console's first READ verb, exercised end to end.

Seals the bundled ontology-exit sample through the console's own driver (no
separate fixture needed — see test_surface_drivers.py::test_ontology_exit_driven),
then queries the sealed shard through axm-core's Spectra engine. Gated on the
axm-genesis kernel (sealing needs it), the axm-core spoke (Spectra lives
there), and duckdb (Spectra's query engine dependency) — mirroring the gating
conventions in test_surface_drivers.py.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from axm_console import Console
from axm_console.ask import ask
from axm_console.cli import main as cli_main
from axm_console.receipt import kernel_available

pytestmark = pytest.mark.skipif(not kernel_available(), reason="axm-genesis kernel not on PATH")


def _core_repo() -> str | None:
    repo = Path(os.environ.get("AXM_CORE_REPO", "/workspace/axm-core"))
    return str(repo) if (repo / "spectra" / "axiom_runtime" / "engine.py").exists() else None


CORE = _core_repo()

try:  # Spectra's query engine dependency
    import duckdb  # noqa: F401

    _HAVE_DUCKDB = True
except Exception:  # pragma: no cover
    _HAVE_DUCKDB = False

requires_duckdb = pytest.mark.skipif(not _HAVE_DUCKDB, reason="duckdb not installed")
requires_core = pytest.mark.skipif(not CORE, reason="axm-core spoke not present")

OBJECT_TYPE_LABELS_SQL = """
    SELECT DISTINCT e.label
    FROM claims c JOIN entities e ON e.entity_id = c.subject
    WHERE e.entity_type = 'object_type'
    ORDER BY e.label
"""


@pytest.fixture(scope="module")
def sealed(tmp_path_factory):
    if not CORE:
        pytest.skip("axm-core spoke not present")
    home = tmp_path_factory.mktemp("ask-home")
    receipt, shard = Console(home).run_surface("ontology-exit", params={"spoke_repo": CORE})
    key = Path(shard).parent / "keys" / "publisher.pub"
    return receipt, Path(shard), key


@requires_core
@requires_duckdb
def test_ask_sql_returns_object_type_labels(sealed):
    receipt, shard, key = sealed
    result = ask(shard, key, sql=OBJECT_TYPE_LABELS_SQL, spoke_repo=CORE)
    assert [r[0] for r in result["rows"]] == [
        "objectType/Aircraft", "objectType/Airport", "objectType/Flight",
    ]
    # The engine's own custody gate derived the same shard id the console did.
    assert result["shard_id"] == receipt.shard_id


@requires_core
def test_ask_without_key_refuses_with_exit_2(sealed, capsys):
    _receipt, shard, _key = sealed
    rc = cli_main(["ask", str(shard), "--sql", "SELECT 1"])
    assert rc == 2
    assert "REFUSED" in capsys.readouterr().err
