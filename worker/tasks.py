
import requests
from celery.signals import task_postrun, task_prerun
from celery import shared_task
import time
import os
from worker.model_inferencing import generate_base_images, inference_model, refine_images
from worker.utils.upload import download_file_from_s3

from worker.utils.utils import delete_file_or_folder


# extract worker dependencies
if os.getenv('CELERY_ENV') != 'server':
    from .model_training import cleanup, prepare_model, train_model


@shared_task(name="test")
def run_test(steps=None, base_model_name=None, subject_type=None, images_zip=None, webhook_url=None):
    start_time = time.time()
    end_time = time.time()
    execution_time = end_time - start_time
    time.sleep(5)
    return {"task_name": "test", "execution_time": execution_time}


@shared_task(name="train-sdxl-dreambooth")
def run_dreambooth(steps=None, base_model_name=None, subject_type=None, images_zip=None, webhook_url=None):
    if os.getenv('CELERY_ENV') != 'server':
        start_time = time.time()
        if not os.path.exists('temp'):
            os.makedirs('temp')
        subject_identifier, instance_prompt = prepare_model(
            subject_type=subject_type, images_zip=images_zip)
        train_model(base_model_name, subject_identifier,
                    instance_prompt, steps)
        cleanup(subject_identifier, steps)
        end_time = time.time()
        execution_time = end_time - start_time
        return {"subject_identifier": subject_identifier, "executionTime": execution_time}
    else:
        start_time = time.time()
        end_time = time.time()
        execution_time = end_time - start_time
        return execution_time


@shared_task(name="inference-sdxl")
def run_inference(prompt=None, steps=None, num_of_images=None, model_id=None, width=None, height=None, base_model_name=None, webhook_url=None):
    if os.getenv('CELERY_ENV') != 'server':
        start_time = time.time()
        images_url = inference_model(prompt,
                                     num_of_images=num_of_images, steps=steps, width=width, height=height, model_id=model_id)
        end_time = time.time()
        execution_time = end_time - start_time
        return {"executionTime": execution_time, "images_url": images_url}
    else:
        start_time = time.time()
        end_time = time.time()
        execution_time = end_time - start_time
        return {"execution_time": execution_time, "images_url": []}


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kw):
    # Extract webhook_url from the task keyword arguments
    webhook_url = kwargs.get('webhook_url')
    data = {"text": "Task started.",
            "task_result": None, "task_status": "STARTED", "task_id": task_id}

    try:
        requests.post(webhook_url, json=data)
    except requests.exceptions.RequestException as e:
        print(f"Failed to send request: {e}")


@task_postrun.connect
def task_done(sender=None, task_id=None, task=None, args=None, state=None, kwargs=None, retval=None, **kw):
    # Extract webhook_url from the task keyword arguments
    webhook_url = kwargs.get('webhook_url')

    print("Task Postrun")
    print("Return value :", type(retval))
    print("State :", state)

    if isinstance(retval, BaseException):
        print("An error occurred during task execution")
        # Hit the webhook
        data = {"text": "Task failed.",
                "task_result": str(retval), "task_status": state, "task_id": task_id}
    else:
        # Hit the webhook
        data = {"text": "Task completed successfully.",
                "task_result": retval, "task_status": state, "task_id": task_id}

    try:
        response = requests.post(webhook_url, json=data)
        # Handle the response if needed
        if response.status_code != 200:
            print(
                f'Error: Request to webhook returned an error {response.status_code}, the response is:\n{response.text}')
    except requests.exceptions.RequestException as e:
        print(f"Failed to send request: {e}")


# # test
# run_dreambooth(
#     steps=100,
#     base_model_name="runwayml/stable-diffusion-v1-5",
#     subject_type="person",
#     images_zip="https://firebasestorage.googleapis.com/v0/b/copykitties-avatar.appspot.com/o/bhumika_aurora.zip?alt=media&token=d0fe3b22-6a59-43e5-ab73-901c60bf0bfe",
#     webhook_url="http://127.0.0.1:8000/webhook"
# )
