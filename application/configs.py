from .config_loader import for_mode

class BaseConfig:
    MONGO_DB = 'syllabits'
    MONGO_URI = 'mongodb://127.0.0.1:27017'

@for_mode('development')
class DevelopmentConfig(BaseConfig):
    DEBUG = True

@for_mode('production')
class ProductionConfig(BaseConfig):
    DEBUG = False
    CORS_ORIGINS = 'api.syllabits.betatesting.as.ua.edu'