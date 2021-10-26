from .config_loader import for_mode

class BaseConfig:
    pass

@for_mode('development')
class DevelopmentConfig(BaseConfig):
    MONGO_URL = 'mongodb://127.0.0.1:27017'

@for_mode('production')
class ProductionConfig(BaseConfig):
    pass