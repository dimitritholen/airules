import configparser
from pathlib import Path

CONFIG_FILENAME = ".rules4rc"


def get_config_path() -> Path:
    """Returns the absolute path to the config file in the current directory."""
    return Path.cwd() / CONFIG_FILENAME


def get_config() -> configparser.ConfigParser:
    """Reads the .rules4rc configuration file."""
    config_path = get_config_path()
    if not config_path.exists():
        raise FileNotFoundError(
            f"{CONFIG_FILENAME} not found in the current directory."
        )

    config = configparser.ConfigParser()
    config.read(config_path)
    return config


def create_default_config():
    """Creates a default .rules4rc file."""
    config = configparser.ConfigParser()
    config["settings"] = {
        "language": "python",
        "tags": "security, best-practices",
        "tools": "cursor, roo, claude, copilot, cline",
    }
    write_config(config)


def write_config(config: configparser.ConfigParser):
    """Writes the configuration to the .rules4rc file."""
    with open(get_config_path(), "w") as configfile:
        config.write(configfile)
