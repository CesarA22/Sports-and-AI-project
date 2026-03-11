"""
Upload processed_bundle.zip para bucket Railway/S3.
Execute após criar o bundle:
  python scripts/generate_sample_data.py
  python scripts/create_bundle.py
  python scripts/upload_bundle_s3.py

Requer .env com S3_ENDPOINT, S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

BUNDLE = PROJECT_ROOT / "data" / "processed_bundle.zip"


def main():
    endpoint = os.getenv("S3_ENDPOINT")
    bucket = os.getenv("S3_BUCKET")
    key = os.getenv("S3_ACCESS_KEY")
    secret = os.getenv("S3_SECRET_KEY")
    if not all([endpoint, bucket, key, secret]):
        print("Configure no .env: S3_ENDPOINT, S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY")
        sys.exit(1)
    if not BUNDLE.exists():
        print(f"Crie o bundle antes: python scripts/create_bundle.py")
        sys.exit(1)

    try:
        import boto3
        from botocore.config import Config
        client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=key,
            aws_secret_access_key=secret,
            config=Config(signature_version="s3v4"),
        )
        key_name = os.getenv("S3_BUNDLE_KEY", "processed_bundle.zip")
        client.upload_file(str(BUNDLE), bucket, key_name)
        print(f"Upload OK: {bucket}/{key_name}")
    except Exception as e:
        print(f"Erro: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
