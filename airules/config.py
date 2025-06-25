import configparser
from pathlib import Path

CONFIG_FILENAME = ".airulesrc"
# Use Path.cwd() to keep the config file in the project's root directory
CONFIG_PATH = Path.cwd() / CONFIG_FILENAME

def write_config(config):
    """Write the config parser object to the .airulesrc file."""
    with open(CONFIG_PATH, 'w') as configfile:
        config.write(configfile)

def get_config():
    """Reads the config file and returns a configparser object."""
    config = configparser.ConfigParser()
    if CONFIG_PATH.exists():
        config.read(CONFIG_PATH)
    return config

def save_config(config):
    """Saves the configparser object to the .airulesrc file."""
    with open(CONFIG_PATH, 'w') as configfile:
        config.write(configfile)

def create_default_config():
    """Creates a default .airulesrc file if one doesn't exist."""
    if CONFIG_PATH.exists():
        return False, CONFIG_PATH # Already exists

    config = configparser.ConfigParser()
    config['settings'] = {
        'language': 'python',
        'tool': 'cursor',
        'primary_model': 'gpt-4-turbo',
        'review_model': 'claude-3-opus-20240229'
    }
    config['topics'] = {
        '# A comma-separated list of topics to generate rules for.': '',
        '# Example: fastapi,pytest,coding style,security': '',
        'tags': 'fastapi,pytest,coding style,security'
    }
    save_config(config)
    return True, CONFIG_PATH
