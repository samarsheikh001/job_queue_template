import os
import random
import torch
from worker.utils.upload import download_file_from_s3, upload_image_and_get_public_url


from worker.utils.utils import delete_file_or_folder

from diffusers import DiffusionPipeline, StableDiffusionXLImg2ImgPipeline
from diffusers.utils import load_image


def generate_base_images(prompt: str, num_images: int, model_id: str, steps: int, width: int, height: int):
    pipe = DiffusionPipeline.from_pretrained(
        "stabilityai/stable-diffusion-xl-base-1.0", torch_dtype=torch.float16, use_safetensors=True, variant="fp16")
    pipe.to("cuda")
    pipe.unet = torch.compile(
        pipe.unet, mode="reduce-overhead", fullgraph=True)
    if model_id is not None:
        pipe.load_lora_weights(f"temp/{model_id}.safetensors")
    images = []
    for _ in range(num_images // 4):
        batch_images = pipe(**get_inputs(prompt, batch_size=4,
                            height=height, width=width, num_inference_steps=steps)).images
        images.extend(batch_images)
    remaining = num_images % 4
    if remaining:
        batch_images = DiffusionPipeline(
            **get_inputs(prompt, batch_size=remaining, height=height, width=width, num_inference_steps=steps)).images
        images.extend(batch_images)

    return images


def get_inputs(prompt, width: int, height: int, batch_size=1, num_inference_steps: int = 50):
    seeds = [random.randint(1, 2**32 - 1) for _ in range(batch_size)]
    generator = [torch.Generator("cuda").manual_seed(seed)
                 for seed in seeds]
    prompts = batch_size * [prompt]
    return {"prompt": prompts, "generator": generator, "num_inference_steps": num_inference_steps, "width": width, "height": height}


def refine_images(prompt, base_images):
    pipe = DiffusionPipeline.from_pretrained(
        "stabilityai/stable-diffusion-xl-refiner-1.0", torch_dtype=torch.float16, use_safetensors=True, variant="fp16")
    pipe.to("cuda")
    pipe.unet = torch.compile(
        pipe.unet, mode="reduce-overhead", fullgraph=True)
    refined_images = []
    for image in base_images:
        image = pipe(prompt=prompt, image=image).images[0]
        refined_images.append(image)
    return refined_images


# def inference_model(prompt, model_id, num_of_images, steps, width, height, use_refiner):
#     if not os.path.exists('temp'):
#         os.makedirs('temp')
#     if model_id is not None:
#         download_file_from_s3(
#             f"{model_id}.safetensors", f"temp/{model_id}.safetensors")
#     generated_images = generate_base_images(
#         prompt=prompt, num_images=num_of_images, model_id=model_id, steps=steps, width=width, height=height)
#     if use_refiner:
#         generated_images = refine_images(base_images=generated_images,
#                                          prompt=prompt)
#     images_urls = []
#     for image in generated_images:
#         uploaded_image_url = upload_image_and_get_public_url(image)
#         images_urls.append(uploaded_image_url)
#     delete_file_or_folder("temp")
#     return images_urls

def inference_model(prompt, negative_prompt, image_url, mask_image_url, width, height, num_outputs, scheduler, num_inference_steps, guidance_scale, prompt_strength, seed, refine_steps, model_id):
    if not os.path.exists('temp'):
        os.makedirs('temp')
    if model_id is not None:
        download_file_from_s3(
            f"{model_id}.safetensors", f"temp/{model_id}.safetensors")
    generated_images = generate_base_images(
        prompt=prompt, num_images=num_outputs, model_id=model_id, steps=num_inference_steps, width=width, height=height)
    if refine_steps > 0:
        generated_images = refine_images(base_images=generated_images,
                                         prompt=prompt)
    images_urls = []
    for image in generated_images:
        uploaded_image_url = upload_image_and_get_public_url(image)
        images_urls.append(uploaded_image_url)
    delete_file_or_folder("temp")
    return images_urls


def img_to_img(url, prompt, num_of_images):
    pipe = StableDiffusionXLImg2ImgPipeline.from_pretrained(
        "stabilityai/stable-diffusion-xl-base-1.0", torch_dtype=torch.float16, variant="fp16", use_safetensors=True
    )
    pipe = pipe.to("cuda")
    # pipe.unet = torch.compile(
    #     pipe.unet, mode="reduce-overhead", fullgraph=True)
    init_image = load_image(url).convert("RGB")
    generated_images = []
    for _ in range(num_of_images):
        batch_images = pipe(prompt, image=init_image,
                            num_inference_steps=50).images
        batch_images[0].save("img.png")
        generated_images.extend(batch_images)
    images_urls = []
    for image in generated_images:
        uploaded_image_url = upload_image_and_get_public_url(image)
        images_urls.append(uploaded_image_url)
    delete_file_or_folder("temp")
    return images_urls
