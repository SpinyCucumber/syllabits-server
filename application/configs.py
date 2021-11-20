from .config_loader import for_mode

class BaseConfig:
    MONGO_DB = 'syllabits'
    MONGO_URI = 'mongodb://127.0.0.1:27017'
    JWT_TOKEN_LOCATION = 'headers'
    JWT_HEADER_TYPE = ''
    CORS_SUPPORTS_CREDENTIALS = True

@for_mode('development')
class DevelopmentConfig(BaseConfig):
    DEBUG = True
    ENABLE_GRAPHIQL = True

@for_mode('production')
class ProductionConfig(BaseConfig):
    DEBUG = False
    ENABLE_GRAPHIQL = False
    CORS_ORIGINS = 'https://syllabits.betatesting.as.ua.edu'
