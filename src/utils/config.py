import os
import sys
import tomli

HOME_DIR: str = os.path.expanduser("~")
CONFIG_FILE: str = os.path.join(HOME_DIR, ".gen-commit")


def read_config():
    if not os.path.exists(CONFIG_FILE):
        print(
            f"Config file not found at {CONFIG_FILE}. Please run `gencommit --init` to create a config file."
        )
        sys.exit(1)

    config = {}
    with open(CONFIG_FILE, "r") as f:
        for line in f:
            key, value = line.strip().split("=", 1)
            config[key] = value
    return config


def read_version_from_pyproject():
    try:
        with open("pyproject.toml", "rb") as f:
            pyproject_data = tomli.load(f)
        return pyproject_data["project"]["version"]
    except (FileNotFoundError, KeyError):
        return "0.0.0"  # Default version if not found
