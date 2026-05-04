import sys

REQUIRED_MAJOR = 3
REQUIRED_MINOR = 12


def main() -> None:
    major = sys.version_info.major
    minor = sys.version_info.minor

    if major != REQUIRED_MAJOR or minor < REQUIRED_MINOR:
        raise TypeError(
            f"This project requires Python {REQUIRED_MAJOR}.{REQUIRED_MINOR}+. "
            f"Found: Python {sys.version}"
        )
    print(">>> Development environment passes all tests!")


if __name__ == "__main__":
    main()
