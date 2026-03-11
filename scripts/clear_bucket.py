"""
Limpa o bucket S3 - remove todos os objetos.
Execute: python scripts/clear_bucket.py

Requer .env com S3_ENDPOINT, S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass


def main():
    endpoint = os.getenv("S3_ENDPOINT")
    bucket = os.getenv("S3_BUCKET")
    key = os.getenv("S3_ACCESS_KEY")
    secret = os.getenv("S3_SECRET_KEY")
    if not all([endpoint, bucket, key, secret]):
        print("Configure no .env: S3_ENDPOINT, S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY")
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
        count = 0
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket):
            for obj in page.get("Contents", []):
                client.delete_object(Bucket=bucket, Key=obj["Key"])
                print(f"Deletado: {obj['Key']}")
                count += 1
        if count == 0:
            print("Bucket vazio, nada para deletar.")
        else:
            print(f"\n{count} objeto(s) removido(s).")
    except Exception as e:
        print(f"Erro: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
