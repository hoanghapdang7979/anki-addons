import sys
from pathlib import Path

# Same reasoning as the other add-ons' tests/conftest.py: the add-on folder
# name has a hyphen (matches Anki's manifest "package" convention), so it
# can't be imported as a normal Python package. Add it to sys.path directly
# so tests can `import checklist` as a top-level module.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
