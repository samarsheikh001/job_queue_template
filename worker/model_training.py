import subprocess
from worker.utils.upload import upload_file_to_s3

from worker.utils.utils import delete_file_or_folder, download_and_extract_zip, generate_identifier
from autotrain.trainers.dreambooth.main import train
from autotrain.trainers.dreambooth.params import DreamBoothTrainingParams


def prepare_model(images_zip) -> str:
    model_id = generate_identifier()
    download_and_extract_zip(
        images_zip, extract_to=f"temp/{model_id}")
    return model_id


def train_model(base_model_name: str, model_id: str, instance_prompt: str, class_prompt: str, steps: int):
    args = DreamBoothTrainingParams(
        model=base_model_name,
        output='temp/output/',
        image_path=f'temp/{model_id}/',
        prompt=instance_prompt,
        class_prompt=class_prompt,
        resolution=1024,
        batch_size=1,
        num_steps=steps,
        fp16=True,
        gradient_accumulation=4,
        lr=1e-4
    )
    train(args)
    # cmd = [
    #     'autotrain', 'dreambooth',
    #     '--model', base_model_name,
    #     '--output', 'temp/output/',
    #     '--image-path', f'temp/{model_id}/',
    #     '--prompt', instance_prompt,
    #     '--class-prompt', class_prompt,
    #     '--resolution', '1024',
    #     '--batch-size', '1',
    #     '--num-steps', str(steps),
    #     '--fp16',
    #     '--gradient-accumulation', '4',
    #     '--lr', '1e-4'
    # ]
    # subprocess.run(cmd)


def cleanup(model_id: str):
    upload_file_to_s3(f"temp/output/pytorch_lora_weights.safetensors",
                      f"{model_id}.safetensors")
    delete_file_or_folder("temp")  # Delete temp folder
