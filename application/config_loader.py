import os

VAR_MODE = 'SYLLABITS_MODE'
modeToConfig = {}

def for_mode(name):
    def wrapper(config):
        modeToConfig[name] = config
        return config
    return wrapper

def load_config(config):
    # Lookup config using application mode
    # Mode is specified by environment variable
    mode = os.environ.get(VAR_MODE)
    if not mode:
        raise RuntimeError(f'{VAR_MODE} not set!')
    config.from_object(modeToConfig[mode])