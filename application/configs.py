from .config_loader import for_mode

class BaseConfig:
    MONGO_DB = 'syllabits'
    MONGO_URI = 'mongodb://127.0.0.1:27017'

@for_mode('development')
class DevelopmentConfig(BaseConfig):
    DEBUG = True
    ENABLE_GRAPHIQL = True

@for_mode('production')
class ProductionConfig(BaseConfig):
    DEBUG = False
    CORS_ORIGINS = 'https://syllabits.betatesting.as.ua.edu'
    ENABLE_GRAPHIQL = False
