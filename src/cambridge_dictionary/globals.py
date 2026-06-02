import gettext
from pathlib import Path

from anki.lang import current_lang
from aqt import mw

from .provider import ProviderManager

# translation
localedir = Path(__file__).parent / "locales"
translation = gettext.translation("dictionary", localedir, languages=[current_lang], fallback=True)
_ = translation.gettext

addon_module = __name__.rsplit(".", 1)[0]
config = mw.addonManager.getConfig(addon_module)

provider_manager = ProviderManager(config)
