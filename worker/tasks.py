from celery import shared_task
from celery.signals import task_postrun, task_prerun
import requests


@shared_task
def run(a=None, b=None, webhook_url=None):
    import time
    time.sleep(5)
    return a / b


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kw):
    # Extract webhook_url from the task keyword arguments
    webhook_url = kwargs.get('webhook_url')
    data = {"text": "Task started.",
            "result": None, "state": "Started"}

    requests.post(webhook_url, json=data)


@task_postrun.connect
def task_done(sender=None, task_id=None, task=None, args=None, state=None, kwargs=None, retval=None, **kw):
    # Extract webhook_url from the task keyword arguments
    webhook_url = kwargs.get('webhook_url')

    print("Return value :", type(retval))

    if isinstance(retval, BaseException):
        print("An error occurred during task execution")
        # Hit the webhook
        data = {"text": "Task failed.",
                "result": str(retval), "state": state}
    else:
        # Hit the webhook
        data = {"text": "Task completed successfully.",
                "result": retval, "state": state}

    response = requests.post(webhook_url, json=data)

    # Handle the response if needed
    if response.status_code != 200:
        raise ValueError(
            'Request to webhook returned an error %s, the response is:\n%s'
            % (response.status_code, response.text)
        )
