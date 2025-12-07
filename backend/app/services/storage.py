import io
import logging

import boto3
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)

# Initialize S3 client for MinIO
s3_client = boto3.client(
    "s3",
    endpoint_url=f"http://{settings.minio_endpoint}",
    aws_access_key_id=settings.minio_access_key,
    aws_secret_access_key=settings.minio_secret_key,
)


def ensure_bucket_exists() -> None:
    """Create the bucket if it doesn't exist."""
    try:
        s3_client.head_bucket(Bucket=settings.minio_bucket_name)
    except ClientError:
        try:
            s3_client.create_bucket(Bucket=settings.minio_bucket_name)
            logger.info(f"Created bucket: {settings.minio_bucket_name}")
        except ClientError as e:
            logger.error(f"Failed to create bucket: {e}")
            raise


def upload_pdf(disclosure_id: str, filename: str, content: bytes) -> str:
    """
    Upload a PDF to MinIO storage.

    Args:
        disclosure_id: UUID of the disclosure
        filename: Original filename
        content: PDF file content as bytes

    Returns:
        Object key in the format: disclosures/{disclosure_id}/{filename}
    """
    ensure_bucket_exists()

    object_key = f"disclosures/{disclosure_id}/{filename}"

    try:
        s3_client.put_object(
            Bucket=settings.minio_bucket_name,
            Key=object_key,
            Body=content,
            ContentType="application/pdf",
        )
        logger.info(f"Uploaded PDF: {object_key}")
        return object_key
    except ClientError as e:
        logger.error(f"Failed to upload PDF: {e}")
        raise


def download_pdf(object_key: str) -> bytes:
    """
    Download a PDF from MinIO storage.

    Args:
        object_key: The object key in MinIO

    Returns:
        PDF content as bytes
    """
    try:
        response = s3_client.get_object(
            Bucket=settings.minio_bucket_name,
            Key=object_key,
        )
        return response["Body"].read()
    except ClientError as e:
        logger.error(f"Failed to download PDF: {e}")
        raise


def delete_pdf(object_key: str) -> None:
    """
    Delete a PDF from MinIO storage.

    Args:
        object_key: The object key in MinIO
    """
    try:
        s3_client.delete_object(
            Bucket=settings.minio_bucket_name,
            Key=object_key,
        )
        logger.info(f"Deleted PDF: {object_key}")
    except ClientError as e:
        logger.error(f"Failed to delete PDF: {e}")
        # Don't raise - deletion failures shouldn't block disclosure deletion
