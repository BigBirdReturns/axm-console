"""Make the package importable without an install (mirrors the sibling spokes)."""
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
