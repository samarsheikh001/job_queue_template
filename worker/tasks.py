import requests
from celery.signals import task_postrun, task_prerun, task_retry
from celery import shared_task, states
import time
import os

# extract worker dependencies
if os.getenv('CELERY_ENV') != 'server':
    from .model_training import cleanup, prepare_model, train_model
    from worker.model_inferencing import ImageGenerator
    from worker.utils.utils import delete_file_or_folder


@shared_task(name="test")
def run_test(webhook_url=None):
    start_time = time.time()
    end_time = time.time()
    execution_time = end_time - start_time
    time.sleep(5)
    return {"task_name": "test", "execution_time": execution_time}


@shared_task(name="train-dreambooth-lora", bind=True)
def run_dreambooth(self, base_model_name=None, steps=None, instance_prompt=None, class_prompt=None, images_zip=None, webhook_url=None):
    if os.getenv('CELERY_ENV') != 'server':
        result = self.AsyncResult(self.request.id)
        if result.state == states.SUCCESS:
            print("Task already succeeded, skipping execution")
            return result.result
        start_time = time.time()
        if not os.path.exists('temp'):
            os.makedirs('temp')
        model_id = prepare_model(images_zip=images_zip)
        train_model(base_model_name=base_model_name, model_id=model_id,
                    instance_prompt=instance_prompt, class_prompt=class_prompt, steps=steps)
        cleanup(model_id=model_id)
        end_time = time.time()
        execution_time = end_time - start_time
        model_download_url = f"https://usc1.contabostorage.com/95ab9410ae4e43479286fec3395fdfe9:dreambooth/models/{model_id}.safetensors"
        return {"model_id": model_id, "model_download_url": model_download_url, "executionTime": execution_time, "inputs": {
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
def inference(model_id=None, operation=None, prompt=None, num_outputs=None, width=None, height=None, n_steps=None, high_noise_frac=None, image_url=None, mask_url=None, prompt_strength=None, webhook_url=None):
    if os.getenv('CELERY_ENV') != 'server':
        start_time = time.time()
        if not os.path.exists('temp'):
            os.makedirs('temp')

        img_gen = ImageGenerator(model_id=model_id)
        generated_images_url = []
        if operation == "text_to_img":
            text_to_text_images = img_gen.generate_base_images(
                prompt, num_outputs, n_steps, high_noise_frac, width, height)
            generated_images_url = text_to_text_images
        elif operation == "inpainting":
            inpainting_images = img_gen.generate_inpainting_image(
                prompt, num_outputs, n_steps, image_url, mask_url)
            generated_images_url = inpainting_images
        elif operation == "img_to_img":
            img_to_imgs = img_gen.generate_image_to_image(
                prompt_strength, prompt, num_outputs, n_steps, high_noise_frac, image_url)
            generated_images_url = img_to_imgs
        delete_file_or_folder("temp")
        end_time = time.time()
        execution_time = end_time - start_time
        return {"executionTime": execution_time, "inputs": {}, "data": generated_images_url}
    else:
        start_time = time.time()
        end_time = time.time()
        execution_time = end_time - start_time
        return execution_time


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


@task_retry.connect
def task_retry_handler(sender=None, request=None, reason=None, einfo=None, **kwargs):
    # Extract webhook_url from the task request
    webhook_url = request.kwargs.get('webhook_url')
    data = {"text": "Task is being retried.",
            "task_status": "RETRY", "task_id": request.id, "inputs": request.kwargs}

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
#     steps=500,
#     base_model_name="cgburgos/sdxl-1-0-base",
#     instance_prompt="a boy samar",
#     class_prompt="a boy",
#     images_zip="https://firebasestorage.googleapis.com/v0/b/copykitties-avatar.appspot.com/o/bhumika_aurora.zip?alt=media&token=d0fe3b22-6a59-43e5-ab73-901c60bf0bfe",
#     webhook_url="http://127.0.0.1:8000/webhook"
# )

# # Generate base images
# operation = "text_to_img"

# prompt = 'moh man, high quality'
# num_outputs = 4
# width = 1024
# height = 1024
# n_steps = 100
# high_noise_frac = 1

# prompt_strength = 0.8

# img_to_img_url = "https://firebasestorage.googleapis.com/v0/b/copykitties-avatar.appspot.com/o/prompthero-prompt-9804e3f26f1.png?alt=media&token=05a699f3-23ed-4564-85ba-21cb7cebae11"
# image_url = "https://raw.githubusercontent.com/CompVis/latent-diffusion/main/data/inpainting_examples/overture-creations-5sI6fQgYIuo.png"
# mask_url = "https://raw.githubusercontent.com/CompVis/latent-diffusion/main/data/inpainting_examples/overture-creations-5sI6fQgYIuo_mask.png"
# inference(operation=operation,
#           prompt=prompt,
#           num_outputs=num_outputs,
#           width=width,
#           height=height,
#           n_steps=n_steps,
#           high_noise_frac=high_noise_frac,
#           image_url=img_to_img_url,
#           mask_url=mask_url,
#           prompt_strength=prompt_strength,
#           webhook_url="")
# for i, image in enumerate(images):
#     image.save(f"image_{i}.png")
