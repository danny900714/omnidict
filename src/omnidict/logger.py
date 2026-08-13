from aqt.addons import AddonManager

addon_module = __name__.rsplit(".", 1)[0]

# AddonManager.get_logger() is a class method. Calling it doesn't require a running Anki instance
logger = AddonManager.get_logger(addon_module)
