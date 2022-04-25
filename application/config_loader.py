import os

VAR_MODE = 'SYLLABITS_MODE'
mode_to_config = {}

def for_mode(mode):
    def wrapper(config):
        mode_to_config[mode] = config
        return config
    return wrapper

def load_config(config):
    # Lookup config using application mode
    # Mode is specified by environment variable
    mode = os.environ.get(VAR_MODE)
    if not mode:
        print(f'{VAR_MODE} not set! Defaulting to \'development\'')
        mode = 'development'
    config.from_object(mode_to_config[mode])