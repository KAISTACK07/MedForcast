"""
Sync local data to Azure Blob Storage.

Uploads raw data and ML outputs to Azure Blob Storage,
mirroring the local directory structure under blob prefixes.

Usage:
    python sync_to_azure.py            # upload both raw + output
    python sync_to_azure.py --raw      # upload only data/raw/
    python sync_to_azure.py --output   # upload only data/output/
"""
import os
import sys
import argparse

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure project root is on the path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from config.settings import (
    AZURE_STORAGE_CONNECTION_STRING,
    AZURE_CONTAINER_NAME,
    DATA_RAW,
    DATA_OUTPUT,
)
from src.cloud.azure_storage import upload_directory, ensure_container
from src.utils.helpers import logger


def main():
    parser = argparse.ArgumentParser(description="Sync local data to Azure Blob Storage")
    parser.add_argument("--raw", action="store_true", help="Upload only data/raw/")
    parser.add_argument("--output", action="store_true", help="Upload only data/output/")
    args = parser.parse_args()

    # Default: upload both
    upload_raw = True
    upload_output = True
    if args.raw or args.output:
        upload_raw = args.raw
        upload_output = args.output

    # ── Pre-flight check ──────────────────────────────────────────────────────
    if not AZURE_STORAGE_CONNECTION_STRING:
        print("=" * 60)
        print("  AZURE SYNC — NOT CONFIGURED")
        print("=" * 60)
        print()
        print("  Set AZURE_STORAGE_CONNECTION_STRING in your .env file.")
        print("  You can find this in the Azure Portal under:")
        print("    Storage Account → Access Keys → Connection String")
        print()
        print("  Exiting without uploading.")
        return

    print("=" * 60)
    print("  PHARMA ANALYTICS — AZURE BLOB STORAGE SYNC")
    print("=" * 60)
    print(f"  Container: {AZURE_CONTAINER_NAME}")
    print()

    # ── Ensure container exists ───────────────────────────────────────────────
    if not ensure_container():
        print("  Failed to create/access container. Check your connection string.")
        return

    # ── Upload raw data ───────────────────────────────────────────────────────
    if upload_raw:
        print(f"\n[1] Uploading raw data → raw/")
        raw_results = upload_directory(DATA_RAW, prefix="raw")
        raw_ok = sum(1 for v in raw_results.values() if v)
        print(f"    {raw_ok}/{len(raw_results)} files uploaded\n")

    # ── Upload ML outputs ─────────────────────────────────────────────────────
    if upload_output:
        print(f"\n[2] Uploading ML outputs → output/")
        out_results = upload_directory(DATA_OUTPUT, prefix="output")
        out_ok = sum(1 for v in out_results.values() if v)
        print(f"    {out_ok}/{len(out_results)} files uploaded\n")

    print("=" * 60)
    print("  SYNC COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
