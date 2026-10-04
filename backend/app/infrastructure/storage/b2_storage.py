import os
import boto3
import logging
from typing import Optional
from botocore.exceptions import ClientError
from app.core.config import settings

logger = logging.getLogger(__name__)


class BackblazeB2Storage:
    """
    Backblaze B2 Object Storage (S3-compatible).
    Free allowance: 10GB storage, 3x egress.
    Falls back to local filesystem when B2 credentials are not configured.
    """

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        key_id: Optional[str] = None,
        app_key: Optional[str] = None,
        bucket_name: str = "checkout-resumes",
        local_dir: str = "/tmp/checkout_storage"
    ):
        self.bucket_name = bucket_name
        self.local_dir = local_dir
        self.has_b2 = bool(endpoint_url and key_id and app_key)
        self.s3_client = None

        if self.has_b2:
            try:
                self.s3_client = boto3.client(
                    "s3",
                    endpoint_url=endpoint_url,
                    aws_access_key_id=key_id,
                    aws_secret_access_key=app_key
                )
            except Exception as e:
                logger.warning(f"Failed to initialize B2 client: {e}. Using local storage fallback.")
                self.has_b2 = False

        if not self.has_b2:
            os.makedirs(self.local_dir, exist_ok=True)

    def upload_file(self, file_bytes: bytes, file_name: str) -> str:
        """Uploads file to Backblaze B2 bucket or local storage fallback, returning URI."""
        if self.has_b2 and self.s3_client:
            try:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=file_name,
                    Body=file_bytes
                )
                return f"b2://{self.bucket_name}/{file_name}"
            except ClientError as e:
                logger.error(f"Backblaze B2 upload error: {e}")

        # Local fallback
        path = os.path.join(self.local_dir, file_name)
        with open(path, "wb") as f:
            f.write(file_bytes)
        return f"file://{path}"

    def download_file(self, file_name: str) -> bytes:
        if self.has_b2 and self.s3_client:
            try:
                obj = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_name)
                return obj["Body"].read()
            except ClientError as e:
                logger.error(f"Backblaze B2 download error: {e}")

        path = os.path.join(self.local_dir, file_name)
        if os.path.exists(path):
            with open(path, "rb") as f:
                return f.read()
        return b""


b2_storage = BackblazeB2Storage(
    endpoint_url=settings.B2_ENDPOINT_URL or os.environ.get("B2_ENDPOINT_URL"),
    key_id=settings.B2_KEY_ID or os.environ.get("B2_KEY_ID"),
    app_key=settings.B2_APPLICATION_KEY or os.environ.get("B2_APPLICATION_KEY"),
    bucket_name=settings.B2_BUCKET_NAME
)
