import configparser
from pathlib import Path

CONFIG_FILENAME = ".airulesrc"

def get_config_path() -> Path:
    """Returns the absolute path to the config file in the current directory."""
    return Path.cwd() / CONFIG_FILENAME

def get_config() -> configparser.ConfigParser:
    """Reads the .airulesrc configuration file."""
    config_path = get_config_path()
    if not config_path.exists():
        raise FileNotFoundError(f"{CONFIG_FILENAME} not found in the current directory.")
    
    config = configparser.ConfigParser()
    config.read(config_path)
    return config

def create_default_config():
    """Creates a default .airulesrc file."""
    config = configparser.ConfigParser()
    config['settings'] = {
        'language': 'python',
        'tags': 'security, best-practices',
        'tools': 'cursor, roo, claude, copilot, cline'
    }
    write_config(config)

def write_config(config: configparser.ConfigParser):
    """Writes the configuration to the .airulesrc file."""
    with open(get_config_path(), 'w') as configfile:
        config.write(configfile)
