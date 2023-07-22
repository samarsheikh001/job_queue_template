import os
from flask import Flask
from celery import Celery, Task

from dotenv import load_dotenv

load_dotenv()


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


app = Flask(__name__)
app.config.from_mapping(
    CELERY=dict(
        broker_url=os.getenv("CELERY_BROKER_URL"),
        result_backend=os.getenv("CELERY_RESULT_BACKEND"),
        task_ignore_result=True,
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        task_track_started=True,
    ),
)
celery_app = celery_init_app(app)
