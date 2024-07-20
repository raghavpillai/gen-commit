import os

HOME_DIR: str = os.path.expanduser("~")
CONFIG_FILE: str = os.path.join(HOME_DIR, ".gen-commit", "config")


def read_config():
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            for line in f:
                key, value = line.strip().split("=", 1)
                config[key] = value

    return config
