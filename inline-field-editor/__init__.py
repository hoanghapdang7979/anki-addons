import logging

# Import order matters here: anki.hooks -> anki.hooks_gen -> anki.cards ->
# anki.collection -> ... -> anki.models hits a circular import in anki
# 26.8.1 if anki.collection hasn't been fully imported yet. Anki's own
# bootstrap always imports anki.collection early (it builds mw.col before
# any add-on loads), so this never surfaces in a real Anki session - only
# when anki.hooks is imported in isolation (e.g. under pytest). Importing
# it first here sidesteps the cycle without patching the anki package.
import anki.collection  # noqa: F401
from anki import hooks

from .editor_hook import edit_field_filter

logger = logging.getLogger(__name__)

hooks.field_filter.append(edit_field_filter)

logger.info("Inline Field Editor loaded")
