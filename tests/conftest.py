"""Load pure forecast modules without a running Home Assistant instance."""
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "neerslagkompas"
custom = types.ModuleType("custom_components")
custom.__path__ = [str(ROOT.parent)]
package = types.ModuleType("custom_components.neerslagkompas")
package.__path__ = [str(ROOT)]
sys.modules.setdefault("custom_components", custom)
sys.modules.setdefault("custom_components.neerslagkompas", package)
