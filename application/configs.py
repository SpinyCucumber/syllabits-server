from .config_loader import for_mode

class BaseConfig:
    MONGO_DB = 'syllabits'

@for_mode('development')
class DevelopmentConfig(BaseConfig):
    MONGO_URI = 'mongodb://127.0.0.1:27017'

@for_mode('production')
class ProductionConfig(BaseConfig):
    pass