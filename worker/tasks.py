
import requests
from celery.signals import task_postrun, task_prerun
from celery import shared_task
import time
import os

# extract worker dependencies
if os.getenv('CELERY_ENV') != 'server':
    from .model_training import cleanup, prepare_model, train_model
    from worker.model_inferencing import inference_model, img_to_img


@shared_task(name="test")
def run_test(steps=None, base_model_name=None, subject_type=None, images_zip=None, webhook_url=None):
    start_time = time.time()
    end_time = time.time()
    execution_time = end_time - start_time
    time.sleep(5)
    return {"task_name": "test", "execution_time": execution_time}


@shared_task(name="train-dreambooth-lora")
def run_dreambooth(base_model_name=None, steps=None, instance_prompt=None, class_prompt=None, images_zip=None, webhook_url=None):
    if os.getenv('CELERY_ENV') != 'server':
        start_time = time.time()
        if not os.path.exists('temp'):
            os.makedirs('temp')
        model_id = prepare_model(images_zip=images_zip)
        train_model(base_model_name=base_model_name, model_id=model_id,
                    instance_prompt=instance_prompt, class_prompt=class_prompt, steps=steps)
        cleanup(model_id=model_id)
        end_time = time.time()
        execution_time = end_time - start_time
        return {"model_id": model_id, "executionTime": execution_time, "inputs": {
            "base_model_name": base_model_name, "steps": steps,
            "instance_prompt": instance_prompt, "class_prompt": class_prompt,
            "images_zip": images_zip, "webhook_url": webhook_url
        }}
    else:
        start_time = time.time()
        end_time = time.time()
        execution_time = end_time - start_time
        return execution_time


@shared_task(name="inference")
def run_inference(prompt=None, use_refiner=None, steps=None, num_of_images=None, model_id=None, width=None, height=None, base_model_name=None, webhook_url=None):
    if os.getenv('CELERY_ENV') != 'server':
        start_time = time.time()
        images_url = inference_model(prompt, model_id=model_id,
                                     num_of_images=num_of_images, steps=steps, width=width, height=height, use_refiner=use_refiner)
        end_time = time.time()
        execution_time = end_time - start_time
        return {"executionTime": execution_time, "images_url": images_url}
    else:
        start_time = time.time()
        end_time = time.time()
        execution_time = end_time - start_time
        return {"execution_time": execution_time, "images_url": []}


@shared_task(name="img-to-img")
def run_img_to_img(prompt=None, use_refiner=None, steps=None, num_of_images=None, model_id=None, width=None, height=None, base_model_name=None, webhook_url=None):
    if os.getenv('CELERY_ENV') != 'server':
        start_time = time.time()
        prompt = "A majestic tiger sitting on a bench"
        url = "https://huggingface.co/datasets/patrickvonplaten/images/resolve/main/aa_xl/000000009.png"
        images_url = img_to_img(url, prompt, 4)
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
            "task_result": None, "task_status": "STARTED", "task_id": task_id, "inputs": kwargs}

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
                "task_result": str(retval), "task_status": state, "task_id": task_id, "inputs": kwargs}
    else:
        # Hit the webhook
        data = {"text": "Task completed successfully.",
                "task_result": retval, "task_status": state, "task_id": task_id, "inputs": kwargs}

    try:
        response = requests.post(webhook_url, json=data)
        # Handle the response if needed
        if response.status_code != 200:
            print(
                f'Error: Request to webhook returned an error {response.status_code}, the response is:\n{response.text}')
    except requests.exceptions.RequestException as e:
        print(f"Failed to send request: {e}")


# test
# run_dreambooth(
#     steps=5,
#     base_model_name="stabilityai/stable-diffusion-xl-base-1.0",
#     instance_prompt="a boy samar",
#     class_prompt="a boy",
#     images_zip="https://firebasestorage.googleapis.com/v0/b/copykitties-avatar.appspot.com/o/bhumika_aurora.zip?alt=media&token=d0fe3b22-6a59-43e5-ab73-901c60bf0bfe",
#     webhook_url="http://127.0.0.1:8000/webhook"
# )

# prompt = "746ee5c870e14b20ad32b49585da9b9f portrait, high quality"
# model_id = "746ee5c870e14b20ad32b49585da9b9f"

# run_inference(prompt, use_refiner=True, steps=30, num_of_images=4,
#               model_id=None, width=1024, height=1024, base_model_name=None, webhook_url=None)

# prompt = "A majestic tiger sitting on a bench"
# url = "https://huggingface.co/datasets/patrickvonplaten/images/resolve/main/aa_xl/000000009.png"
# img_to_img(url, prompt, 4)
prompt = "746ee5c870e14b20ad32b49585da9b9f portrait, high quality"
negative_prompt = "ugly"
model_id = "746ee5c870e14b20ad32b49585da9b9f"

# run_inference(prompt, use_refiner=True, steps=30, num_of_images=4,
#               model_id=None, width=1024, height=1024, base_model_name=None, webhook_url=None)

inference_model(prompt=prompt, negative_prompt=negative_prompt,
                image_url=None, mask_image_url=None, width=1024, height=1024, num_outputs=4, scheduler=None,
                num_inference_steps=25, guidance_scale=1, prompt_strength=0.8, seed=1, refine_steps=20, model_id=None)
