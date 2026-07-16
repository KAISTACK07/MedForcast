"""
Azure Blob Storage client for the Pharma Analytics platform.

Provides upload, download, list, and delete operations against
Azure Blob Storage. Gracefully degrades when no connection string
is configured — functions log a warning and return without crashing.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from config.settings import AZURE_STORAGE_CONNECTION_STRING, AZURE_CONTAINER_NAME
from src.utils.helpers import logger

# Lazy import — only loaded when a function is actually called
_blob_service_client = None


def _is_configured() -> bool:
    """Check whether Azure credentials are present."""
    if not AZURE_STORAGE_CONNECTION_STRING:
        logger.warning(
            "Azure Storage not configured — set AZURE_STORAGE_CONNECTION_STRING in .env"
        )
        return False
    return True


def get_blob_service_client():
    """
    Create (or return cached) BlobServiceClient from the connection string.
    Returns None if not configured.
    """
    global _blob_service_client
    if _blob_service_client is not None:
        return _blob_service_client

    if not _is_configured():
        return None

    from azure.storage.blob import BlobServiceClient

    _blob_service_client = BlobServiceClient.from_connection_string(
        AZURE_STORAGE_CONNECTION_STRING
    )
    logger.info("Azure BlobServiceClient initialised")
    return _blob_service_client


def ensure_container(container_name: str = AZURE_CONTAINER_NAME) -> bool:
    """
    Create the blob container if it does not already exist.
    Returns True if the container is ready, False otherwise.
    """
    client = get_blob_service_client()
    if client is None:
        return False

    try:
        container_client = client.get_container_client(container_name)
        if not container_client.exists():
            client.create_container(container_name)
            logger.info(f"Created Azure container: {container_name}")
        else:
            logger.info(f"Azure container already exists: {container_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to ensure container '{container_name}': {e}")
        return False


# ── Single-file operations ────────────────────────────────────────────────────


def upload_file(
    local_path: str,
    blob_name: str = None,
    container_name: str = AZURE_CONTAINER_NAME,
    overwrite: bool = True,
) -> bool:
    """
    Upload a single local file to Azure Blob Storage.

    Args:
        local_path:      Absolute or relative path to the file on disk.
        blob_name:       Name of the blob in the container.
                         Defaults to the file's basename.
        container_name:  Target container (defaults to settings value).
        overwrite:       Whether to overwrite an existing blob.

    Returns True on success, False on failure or if not configured.
    """
    client = get_blob_service_client()
    if client is None:
        return False

    if not os.path.exists(local_path):
        logger.warning(f"File not found, skipping upload: {local_path}")
        return False

    if blob_name is None:
        blob_name = os.path.basename(local_path)

    try:
        blob_client = client.get_container_client(container_name).get_blob_client(
            blob_name
        )
        with open(local_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=overwrite)

        size_kb = os.path.getsize(local_path) / 1024
        logger.info(f"☁️  Uploaded {blob_name} ({size_kb:.1f} KB)")
        return True
    except Exception as e:
        logger.error(f"Failed to upload {local_path} → {blob_name}: {e}")
        return False


def download_file(
    blob_name: str,
    local_path: str,
    container_name: str = AZURE_CONTAINER_NAME,
) -> bool:
    """
    Download a single blob to a local path.

    Returns True on success, False on failure or if not configured.
    """
    client = get_blob_service_client()
    if client is None:
        return False

    try:
        os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
        blob_client = client.get_container_client(container_name).get_blob_client(
            blob_name
        )
        with open(local_path, "wb") as f:
            stream = blob_client.download_blob()
            stream.readinto(f)

        size_kb = os.path.getsize(local_path) / 1024
        logger.info(f"☁️  Downloaded {blob_name} → {local_path} ({size_kb:.1f} KB)")
        return True
    except Exception as e:
        logger.error(f"Failed to download {blob_name}: {e}")
        return False


# ── Bulk operations ───────────────────────────────────────────────────────────


def upload_directory(
    local_dir: str,
    prefix: str = "",
    container_name: str = AZURE_CONTAINER_NAME,
    overwrite: bool = True,
) -> dict:
    """
    Upload every file in *local_dir* to the container under *prefix/*.

    Returns a dict of {blob_name: success_bool}.
    """
    if not _is_configured():
        return {}

    ensure_container(container_name)

    results = {}
    if not os.path.isdir(local_dir):
        logger.warning(f"Directory not found: {local_dir}")
        return results

    for filename in sorted(os.listdir(local_dir)):
        filepath = os.path.join(local_dir, filename)
        if not os.path.isfile(filepath):
            continue  # skip subdirectories

        blob_name = f"{prefix}/{filename}" if prefix else filename
        results[blob_name] = upload_file(
            filepath, blob_name, container_name, overwrite
        )

    uploaded = sum(1 for v in results.values() if v)
    logger.info(
        f"Bulk upload complete: {uploaded}/{len(results)} files → {prefix or '/'}"
    )
    return results


def download_directory(
    prefix: str,
    local_dir: str,
    container_name: str = AZURE_CONTAINER_NAME,
) -> dict:
    """
    Download all blobs under *prefix* to *local_dir*.

    Returns a dict of {blob_name: success_bool}.
    """
    client = get_blob_service_client()
    if client is None:
        return {}

    results = {}
    os.makedirs(local_dir, exist_ok=True)
    container_client = client.get_container_client(container_name)

    for blob in container_client.list_blobs(name_starts_with=prefix):
        # Strip the prefix to get a flat local filename
        local_name = blob.name
        if prefix:
            local_name = blob.name[len(prefix) :].lstrip("/")
        local_path = os.path.join(local_dir, local_name)
        results[blob.name] = download_file(blob.name, local_path, container_name)

    downloaded = sum(1 for v in results.values() if v)
    logger.info(
        f"Bulk download complete: {downloaded}/{len(results)} files → {local_dir}"
    )
    return results


# ── Listing & deletion ────────────────────────────────────────────────────────


def list_blobs(
    prefix: str = "",
    container_name: str = AZURE_CONTAINER_NAME,
) -> list:
    """
    List blob names in the container, optionally filtered by prefix.
    Returns an empty list if not configured.
    """
    client = get_blob_service_client()
    if client is None:
        return []

    container_client = client.get_container_client(container_name)
    return [blob.name for blob in container_client.list_blobs(name_starts_with=prefix)]


def delete_blob(
    blob_name: str,
    container_name: str = AZURE_CONTAINER_NAME,
) -> bool:
    """Delete a single blob. Returns True on success."""
    client = get_blob_service_client()
    if client is None:
        return False

    try:
        client.get_container_client(container_name).delete_blob(blob_name)
        logger.info(f"🗑️  Deleted blob: {blob_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete {blob_name}: {e}")
        return False
