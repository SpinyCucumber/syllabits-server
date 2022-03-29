from .config_loader import for_mode

class BaseConfig:
    MONGO_DB = 'syllabits'
    MONGO_URI = 'mongodb://127.0.0.1:27017'
    JWT_TOKEN_LOCATION = 'headers'
    JWT_HEADER_TYPE = ''
    # No need to send cookies when making third-party requests
    JWT_COOKIE_SAMESITE = 'strict'
    CORS_SUPPORTS_CREDENTIALS = True

@for_mode('development')
class DevelopmentConfig(BaseConfig):
    DEBUG = True
    ENABLE_GRAPHIQL = True

@for_mode('betatesting')
class BetaTestingConfig(BaseConfig):
    DEBUG = False
    ENABLE_GRAPHIQL = False
    JWT_COOKIE_SECURE = True
    CORS_ORIGINS = 'https://syllabits.betatesting.as.ua.edu'

@for_mode('production')
class ProductionConfig(BaseConfig):
    DEBUG = False
    ENABLE_GRAPHIQL = False
    JWT_COOKIE_SECURE = True
    CORS_ORIGINS = 'https://syllabits.as.ua.edu'
