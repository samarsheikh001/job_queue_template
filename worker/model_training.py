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
        lr=1e-4,
        xl=True,
    )
    train(args)
    # args = DreamBoothTrainingParams(
    #     model="stabilityai/stable-diffusion-xl-base-1.0",
    #     prompt="a photo of a girl danica",
    #     class_prompt="a photo of a girl",
    #     image_path=f'temp/{model_id}/',
    #     num_steps=5,
    #     # Required fields with default values
    #     revision=None,
    #     tokenizer=None,
    #     class_image_path=None,
    #     num_class_images=100,
    #     class_labels_conditioning=None,
    #     prior_preservation=False,
    #     prior_loss_weight=1.0,
    #     output="dreambooth-model",
    #     seed=42,
    #     resolution=512,
    #     center_crop=False,
    #     train_text_encoder=False,
    #     batch_size=4,
    #     sample_batch_size=4,
    #     epochs=1,
    #     checkpointing_steps=500,
    #     resume_from_checkpoint=None,
    #     gradient_accumulation=1,
    #     gradient_checkpointing=False,
    #     lr=5e-4,
    #     scale_lr=False,
    #     scheduler="constant",
    #     warmup_steps=0,
    #     num_cycles=1,
    #     lr_power=1.0,
    #     dataloader_num_workers=0,
    #     use_8bit_adam=False,
    #     adam_beta1=0.9,
    #     adam_beta2=0.999,
    #     adam_weight_decay=1e-2,
    #     adam_epsilon=1e-8,
    #     max_grad_norm=1.0,
    #     allow_tf32=False,
    #     prior_generation_precision=None,
    #     local_rank=-1,
    #     xformers=False,
    #     pre_compute_text_embeddings=False,
    #     tokenizer_max_length=None,
    #     text_encoder_use_attention_mask=False,
    #     rank=4,
    #     xl=True,
    #     fp16=True,
    #     bf16=False,
    #     hub_token=None,
    #     hub_model_id=None,
    #     push_to_hub=False,
    #     validation_prompt=None,
    #     num_validation_images=4,
    #     validation_epochs=50,
    #     checkpoints_total_limit=None,
    #     validation_images=None,
    #     logging=False,
    # )
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
