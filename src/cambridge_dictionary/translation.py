import gettext
from pathlib import Path

from anki import lang

localedir = Path(__file__).parent / "locales"
translation = gettext.translation("dictionary", localedir, languages=[lang.current_lang], fallback=True)
translation.install()

_ = translation.gettext
