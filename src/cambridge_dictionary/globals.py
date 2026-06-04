import gettext
from pathlib import Path

from anki.lang import current_lang
from aqt import mw

from .provider import ProviderManager

# translation
localedir = Path(__file__).parent / "locales"
translation = gettext.translation("dictionary", localedir, languages=[current_lang], fallback=True)
_ = translation.gettext

provider_manager = ProviderManager()

# Addon information
addon_module = __name__.rsplit(".", 1)[0]
addon_package = mw.addonManager.addonFromModule(addon_module)
config = mw.addonManager.getConfig(addon_module)
mw.addonManager.setWebExports(addon_module, r"web/.*(css|js)")

def on_config_updated(new_config: dict):
    # Update global config
    global config
    config = new_config

    # Remove all instantiated provider so that providers get the updated config
    global provider_manager
    provider_manager.clear_providers()


# Handle config update
mw.addonManager.setConfigUpdatedAction(addon_module, on_config_updated)