import os
import random
import torch
from worker.utils.upload import download_file_from_s3, upload_image_and_get_public_url


from worker.utils.utils import delete_file_or_folder

from diffusers import DiffusionPipeline, StableDiffusionXLImg2ImgPipeline, StableDiffusionXLInpaintPipeline
from diffusers.utils import load_image


class ImageGenerator:
    def __init__(self, model_id=None):
        self.model_id = model_id
        if not os.path.exists('temp'):
            os.makedirs('temp')
        if self.model_id is not None:
            download_file_from_s3(
                f"{self.model_id}.safetensors", f"temp/{self.model_id}.safetensors")

    def generate_base_images(self, prompt: str, num_outputs: int, num_inference_steps: int, high_noise_frac: float, width: int, height: int):
        base = DiffusionPipeline.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0", torch_dtype=torch.float16, variant="fp16", use_safetensors=True
        )
        base.to("cuda")
        refiner = DiffusionPipeline.from_pretrained(
            "stabilityai/stable-diffusion-xl-refiner-1.0",
            text_encoder_2=base.text_encoder_2,
            vae=base.vae,
            torch_dtype=torch.float16,
            use_safetensors=True,
            variant="fp16",
        )
        refiner.to("cuda")
        # pipe.unet = torch.compile(
        #     pipe.unet, mode="reduce-overhead", fullgraph=True)
        if self.model_id is not None:
            base.load_lora_weights(f"temp/{self.model_id}.safetensors")
        images = []
        for _ in range(num_outputs):
            image = base(
                prompt=prompt,
                width=width,
                height=height,
                num_inference_steps=num_inference_steps,
                denoising_end=high_noise_frac,
                output_type="latent",
            ).images
            image = refiner(
                prompt=prompt,
                num_inference_steps=num_inference_steps,
                denoising_start=high_noise_frac,
                image=image,
            ).images[0]
            images.append(image)
        images_urls = []
        for image in images:
            uploaded_image_url = upload_image_and_get_public_url(image)
            images_urls.append(uploaded_image_url)
        delete_file_or_folder("temp")
        return images_urls

    def generate_image_to_image(self, prompt_strength: float, prompt: str, num_outputs: int, num_inference_steps: int, high_noise_frac: float, image_url: str):
        init_image = load_image(image_url).convert("RGB")
        base = StableDiffusionXLImg2ImgPipeline.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0", torch_dtype=torch.float16, variant="fp16", use_safetensors=True
        )
        base = base.to("cuda")
        if self.model_id is not None:
            base.load_lora_weights(f"temp/{self.model_id}.safetensors")
        images = []
        for _ in range(num_outputs):
            image = base(prompt,
                         image=init_image,
                         strength=prompt_strength,
                         num_inference_steps=num_inference_steps,
                         ).images[0]
            images.append(image)
        images_urls = []
        for image in images:
            uploaded_image_url = upload_image_and_get_public_url(image)
            images_urls.append(uploaded_image_url)
        return images_urls

    def generate_inpainting_image(self, prompt: str, num_outputs: int, num_inference_steps: int, image_url: str, mask_url: str):
        init_image = load_image(image_url).convert("RGB")
        mask_image = load_image(mask_url).convert("RGB")
        pipe = StableDiffusionXLInpaintPipeline.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0", torch_dtype=torch.float16, variant="fp16", use_safetensors=True
        )
        pipe.to("cuda")
        if self.model_id is not None:
            pipe.load_lora_weights(f"temp/{self.model_id}.safetensors")
        images = []
        for _ in range(num_outputs):
            image = pipe(prompt=prompt, image=init_image, mask_image=mask_image,
                         num_inference_steps=num_inference_steps).images[0]
            images.append(image)
        images_urls = []
        for image in images:
            uploaded_image_url = upload_image_and_get_public_url(image)
            images_urls.append(uploaded_image_url)
        return images_urls
