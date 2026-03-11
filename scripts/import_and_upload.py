"""
Importa dados localmente (sem scraping), cria o bundle e faz upload para o bucket.

Fluxo:
  1. Gera dados de exemplo em data/processed/ (ou use seus próprios parquets)
  2. Cria processed_bundle.zip
  3. Faz upload para o bucket S3

Execute:
  python scripts/import_and_upload.py

Com --skip-generate: pula passo 1 (use se já tem parquets em data/processed/)
  python scripts/import_and_upload.py --skip-generate

Requer .env com S3_ENDPOINT, S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY
"""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
sys.path.insert(0, str(PROJECT_ROOT))

# Carregar .env
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass


def _has_required_data() -> bool:
    required = ["master.parquet", "features.parquet", "umap_clusters.parquet", "outliers.parquet"]
    return all((DATA_DIR / f).exists() for f in required)


def main():
    skip_generate = "--skip-generate" in sys.argv

    # 1) Gerar dados (sample - sem scraping) ou usar existentes
    if not skip_generate:
        print("1/3 Gerando dados em data/processed/...")
        sample_script = PROJECT_ROOT / "scripts" / "generate_sample_data.py"
        if not sample_script.exists():
            print("Erro: scripts/generate_sample_data.py não encontrado")
            sys.exit(1)
        r = subprocess.run([sys.executable, str(sample_script)], cwd=str(PROJECT_ROOT), capture_output=True, text=True)
        if r.returncode != 0:
            print(f"Erro ao gerar dados: {r.stderr or r.stdout}")
            sys.exit(1)
        print("   OK")
    else:
        if not _has_required_data():
            print("Erro: data/processed/ não tem os parquets necessários. Rode sem --skip-generate primeiro.")
            sys.exit(1)
        print("1/3 Usando dados existentes em data/processed/")

    # 2) Criar bundle
    print("2/3 Criando bundle...")
    bundle_script = PROJECT_ROOT / "scripts" / "create_bundle.py"
    r = subprocess.run([sys.executable, str(bundle_script)], cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    if r.returncode != 0:
        print(f"Erro ao criar bundle: {r.stderr or r.stdout}")
        sys.exit(1)
    print(r.stdout.strip())

    # 3) Upload para bucket
    print("3/3 Upload para bucket...")
    upload_script = PROJECT_ROOT / "scripts" / "upload_bundle_s3.py"
    r = subprocess.run([sys.executable, str(upload_script)], cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    if r.returncode != 0:
        print(f"Erro no upload: {r.stderr or r.stdout}")
        sys.exit(1)
    print(r.stdout.strip())
    print("\nConcluído. O app com DATA_MODE=download carregará os dados do bucket.")


if __name__ == "__main__":
    main()
