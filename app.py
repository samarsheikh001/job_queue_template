from worker import tasks
from project import create_app, ext_celery
from dotenv import load_dotenv
load_dotenv()


app = create_app()
celery = ext_celery.celery
