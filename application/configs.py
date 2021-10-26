from .config_loader import for_mode

class BaseConfig:
    pass

@for_mode('development')
class DevelopmentConfig(BaseConfig):
    pass

@for_mode('production')
class ProductionConfig(BaseConfig):
    pass