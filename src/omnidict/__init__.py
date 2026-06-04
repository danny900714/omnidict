# Include vendor directory into sys.path
import sys
from pathlib import Path

vendor_path = str(Path(__file__).parent / "vendor")
if vendor_path not in sys.path:
    sys.path.insert(0, vendor_path)

from . import editor
