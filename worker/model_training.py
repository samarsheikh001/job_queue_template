import subprocess
from worker.utils.upload import upload_file_to_s3

from worker.utils.utils import delete_file_or_folder, download_and_extract_zip, generate_identifier


def prepare_model(subject_type, images_zip) -> str:
    instance_prompt = "a photo of a person" if subject_type == "person" else "Unknown subject type"
    subject_identifier = generate_identifier()
    download_and_extract_zip(
        images_zip, extract_to=f"temp/{subject_identifier}")
    return subject_identifier, instance_prompt


def train_model(base_model_name: str, subject_identifier: str, instance_prompt: str, steps: int):
    cmd = [
        'autotrain', 'dreambooth',
        '--model', 'stabilityai/stable-diffusion-xl-base-1.0',
        '--output', 'temp/output/',
        '--image-path', f'temp/{subject_identifier}/',
        '--prompt', f'{instance_prompt} {subject_identifier}',
        '--resolution', '1024',
        '--batch-size', '1',
        '--num-steps', '500',
        '--fp16',
        '--gradient-accumulation', '4',
        '--lr', '1e-4'
    ]
    subprocess.run(cmd)


def cleanup(subject_identifier: str, steps: int):
    upload_file_to_s3(f"temp/output/pytorch_lora_weights.safetensors",
                      f"{subject_identifier}.safetensors")
    delete_file_or_folder("temp")  # Delete temp folder
