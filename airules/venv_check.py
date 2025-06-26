import sys


def in_virtualenv():
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )


def main():
    if not in_virtualenv():
        print(
            "[airules] ERROR: Please activate a virtual environment before running airules."
        )
        sys.exit(1)
    print("[airules] Virtual environment detected.")


if __name__ == "__main__":
    main()
