import subprocess
from pathlib import Path


def main():
    locales_dir = Path(__file__).parent.parent.joinpath("locales")
    addon_locales_dir = Path(__file__).parent.parent.joinpath(
        "src", "omnidict", "locales"
    )

    for language_dir in locales_dir.iterdir():
        if language_dir.is_dir():
            language = language_dir.name

            # Create dir in src/omnidict/locales/<language>/LC_MESSAGES if it doesn't exist
            addon_language_dir = addon_locales_dir.joinpath(language)
            addon_lc_messages_dir = addon_language_dir.joinpath("LC_MESSAGES")
            if not addon_lc_messages_dir.exists():
                addon_lc_messages_dir.mkdir(parents=True)

            for po_path in language_dir.glob("LC_MESSAGES/*.po"):
                mo_path = addon_lc_messages_dir.joinpath(f"{po_path.stem}.mo")

                print(f"Compiling {po_path} to {mo_path}")
                subprocess.run(["msgfmt", "-o", mo_path, po_path], timeout=10)


if __name__ == "__main__":
    main()
