#!/bin/bash
# SessionStart bootstrap for Claude Code on the web.
#
# Brings up the pinned axm-genesis kernel WITHOUT pip-from-git (which some
# sandboxes block): clone the kernel repo at the pinned v1.0.0 commit, install
# only PyPI dependencies (plus playwright for the interface-procedure driver;
# the web container ships Chromium pre-installed), and expose axm-build /
# axm-verify / axm as thin from-source wrappers. After this hook, the console
# core suite runs kernel-backed with:
#     python -m pytest tests/ -q
# (driver tests that need sibling spoke repos still skip unless those repos
# are checked out and AXM_*_REPO point at them — that is by design.)
#
# Idempotent; safe to re-run. Web sessions only.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Pinned by full commit hash (axm-genesis v1.0.0) per the ledger release
# policy — the same pin as pyproject.toml. Bump deliberately.
GENESIS_PIN="9074e7fb2e9cedde692b248cdd0c6a805e77d8ac"
BOOT="$HOME/.axm-bootstrap"
GEN="$BOOT/axm-genesis"
BIN="$BOOT/bin"
mkdir -p "$BIN"

# 1. Kernel source at the pin. Full clone (the pin is not the branch tip, so a
#    shallow clone cannot reach it); reused if already present.
if [ ! -f "$GEN/src/axm_build/cli.py" ]; then
  rm -rf "$GEN"
  git clone --quiet https://github.com/BigBirdReturns/axm-genesis "$GEN"
fi
git -C "$GEN" -c advice.detachedHead=false checkout --quiet "$GENESIS_PIN"

# 2. PyPI dependencies only — kernel runtime deps, pytest, playwright.
python3 -m pip install --quiet --user \
  blake3 pynacl click 'dilithium-py>=0.5.0' pytest playwright

# 3. Thin CLI wrappers (kernel and console run from source, not installed).
for spec in axm-build:axm_build.cli axm-verify:axm_verify.cli; do
  name="${spec%%:*}"
  mod="${spec##*:}"
  cat > "$BIN/$name" <<WRAP
#!/bin/sh
export PYTHONPATH="$GEN/src\${PYTHONPATH:+:\$PYTHONPATH}"
exec python3 -c "from $mod import main; main()" "\$@"
WRAP
  chmod +x "$BIN/$name"
done
cat > "$BIN/axm" <<WRAP
#!/bin/sh
export PYTHONPATH="$CLAUDE_PROJECT_DIR:$GEN/src\${PYTHONPATH:+:\$PYTHONPATH}"
exec python3 -c "from axm_console.cli import main; main()" "\$@"
WRAP
chmod +x "$BIN/axm"

# 4. Persist the environment for the whole session.
{
  echo "export PATH=\"$BIN:\$PATH\""
  echo "export PYTHONPATH=\"$CLAUDE_PROJECT_DIR:$GEN/src\${PYTHONPATH:+:\$PYTHONPATH}\""
} >> "$CLAUDE_ENV_FILE"

echo "axm bootstrap: kernel @ ${GENESIS_PIN:0:7} from source; axm/axm-build/axm-verify on PATH" >&2
