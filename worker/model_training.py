import subprocess
from worker.utils.upload import upload_file_to_s3

from worker.utils.utils import delete_file_or_folder, download_and_extract_zip, generate_identifier
from worker.utils.to_ckpt import convert_model


def prepare_model(subject_type, images_zip) -> str:
    instance_prompt = "a photo of a person" if subject_type == "person" else "Unknown subject type"
    subject_identifier = generate_identifier()
    download_and_extract_zip(
        images_zip, extract_to=f"temp/{subject_identifier}")
    return subject_identifier, instance_prompt


def train_model(base_model_name: str, subject_identifier: str, instance_prompt: str, steps: int):
    cmd = [
        "accelerate",
        "launch",
        "worker/train_dreambooth.py",
        "--pretrained_model_name_or_path", base_model_name,
        "--instance_data_dir", f"temp/{subject_identifier}",
        "--output_dir", "temp/output",
        "--instance_prompt", f"{instance_prompt} {subject_identifier}",
        "--resolution", "512",
        "--train_batch_size", "1",
        "--gradient_accumulation_steps", "1",
        "--learning_rate", "2e-6",
        "--lr_scheduler", "constant",
        "--lr_warmup_steps", "0",
        "--max_train_steps", str(steps),
    ]
    subprocess.run(cmd)


def cleanup(subject_identifier: str, steps: int):
    convert_model(f"temp/output/{steps}",
                  f"temp/{subject_identifier}.ckpt", True)
    upload_file_to_s3(f"temp/{subject_identifier}.ckpt",
                      f"{subject_identifier}.ckpt")
    delete_file_or_folder("temp")  # Delete temp folder
