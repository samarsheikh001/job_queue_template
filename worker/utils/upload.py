from io import BytesIO
import os
import uuid
import boto3
from dotenv import load_dotenv
load_dotenv()

s3 = boto3.resource(
    's3',
    endpoint_url=os.getenv("S3_ENDPOINT_URL"),
    aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY")
)

s3_client = boto3.client(
    's3',
    endpoint_url=os.getenv("S3_ENDPOINT_URL"),
    aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY")
)

bucket_name = "generated-images"
bucket = s3.Bucket('models')


def upload_file_to_s3(file_path, s3_key):
    try:
        bucket.upload_file(file_path, s3_key)
        print("File uploaded successfully!")
    except Exception as e:
        print(f"Error uploading file: {e}")
        raise


def download_file_from_s3(s3_key, file_path):
    try:
        bucket.download_file(s3_key, file_path)
        print("File downloaded successfully!")
    except Exception as e:
        print(f"Error downloading file: {e}")


def upload_image_to_s3(pil_image, s3_key):
    try:
        byte_stream = BytesIO()
        # you can change format as needed
        pil_image.save(byte_stream, format='PNG')
        byte_stream.seek(0)  # rewind the file pointer
        s3_client.upload_fileobj(byte_stream, bucket_name, s3_key)
        print("Image uploaded successfully!")
    except Exception as e:
        print(f"Error uploading image: {e}")
        raise


def upload_image_and_get_public_url(pil_image):
    s3_key = uuid.uuid4()
    try:
        upload_image_to_s3(pil_image, f"{s3_key}.png")
        print("Image uploaded successfully!")
        print(
            f"Image made public. URL: https://usc1.contabostorage.com/95ab9410ae4e43479286fec3395fdfe9:models/{bucket_name}/{s3_key}.png")
        return f"https://usc1.contabostorage.com/95ab9410ae4e43479286fec3395fdfe9:models/{bucket_name}/{s3_key}.png"

    except Exception as e:
        print(f"Error uploading image or making it public: {e}")
        raise
