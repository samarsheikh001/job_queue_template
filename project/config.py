import os
from pathlib import Path


class BaseConfig:
    """Base configuration"""
    BASE_DIR = Path(__file__).parent.parent
    TESTING = False

    CELERY_BROKER_URL = os.environ.get(
        "CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
    CELERY_RESULT_BACKEND = os.environ.get(
        "CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/0")
    CELERY_ACKS_LATE = True
    CELERY_TASK_TRACK_STARTED = True
    CELERYD_PREFETCH_MULTIPLIER = 1
    BROKER_USE_SSL = True
    # CELERY_TASK_ALWAYS_EAGER = True


class DevelopmentConfig(BaseConfig):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(BaseConfig):
    """Production configuration"""
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
