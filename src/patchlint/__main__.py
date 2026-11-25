"""Allow ``python -m patchlint``."""

from patchlint.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
