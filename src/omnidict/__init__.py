# Include vendor directory into sys.path
import sys
from pathlib import Path

vendor_path = str(Path(__file__).parent / "vendor")
if vendor_path not in sys.path:
    sys.path.insert(0, vendor_path)

# ruff: disable[E402]
from . import editor  # noqa: F401
# ruff: enable[E402]
