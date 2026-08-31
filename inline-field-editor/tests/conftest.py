import sys
from pathlib import Path

# The add-on folder name contains a hyphen (matches Anki's manifest "package"
# convention), so it can't be imported as a normal Python package. Add it to
# sys.path directly so tests can `import editor_hook` as a top-level module.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
