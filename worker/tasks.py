import os
from celery import shared_task
from celery.signals import task_postrun, task_prerun
import requests
from dotenv import load_dotenv
load_dotenv()
# extract worker dependencies
if os.getenv('CELERY_ENV') != 'server':
    from .model_training import cleanup, prepare_model, train_model


@shared_task
def run(steps=None, base_model_name=None, subject_type=None, images_zip=None, webhook_url=None):
    if os.getenv('CELERY_ENV') != 'server':
        try:
            if not os.path.exists('temp'):
                os.makedirs('temp')
            subject_identifier, instance_prompt = prepare_model(
                subject_type=subject_type, images_zip=images_zip)
            train_model(base_model_name, subject_identifier,
                        instance_prompt, steps)
            cleanup(subject_identifier, steps)
            return subject_identifier

        except Exception as e:
            print(f"Error encountered: {e}")
            return {"error": 1}
    else:
        return {}


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


# # test
# run(
#     steps=100,
#     base_model_name="runwayml/stable-diffusion-v1-5",
#     subject_type="person",
#     images_zip="https://firebasestorage.googleapis.com/v0/b/copykitties-avatar.appspot.com/o/bhumika_aurora.zip?alt=media&token=d0fe3b22-6a59-43e5-ab73-901c60bf0bfe",
#     webhook_url="http://127.0.0.1:8000/webhook"
# )
