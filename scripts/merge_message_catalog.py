import subprocess
import sys
from pathlib import Path


def main():
    locales_dir = Path(__file__).parent.parent.joinpath("locales")
    pot_path = locales_dir.joinpath("omnidict.pot")
    if not pot_path.is_file():
        print(f"Cannot find {pot_path} file.")
        sys.exit(1)

    for po_path in locales_dir.glob("*/LC_MESSAGES/*.po"):
        print(f"Execute megmerge --update --sort-by-file {po_path} {pot_path}")
        subprocess.run(
            ["msgmerge", "--update", "--sort-by-file", po_path, pot_path],
            check=True,
            timeout=10,
        )


if __name__ == "__main__":
    main()
