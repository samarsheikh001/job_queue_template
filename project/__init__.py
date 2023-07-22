import os

from flask import Flask
from flask_celeryext import FlaskCeleryExt
from project.config import config

from project.celery_utils import make_celery
ext_celery = FlaskCeleryExt(create_celery_app=make_celery)  # new


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_CONFIG", "development")

    # instantiate the app
    app = Flask(__name__)

    # set config
    app.config.from_object(config[config_name])

    # set extensions
    ext_celery.init_app(app)  # new

    # shell context for flask cli
    @app.shell_context_processor
    def ctx():
        return {"app": app}

    return app
