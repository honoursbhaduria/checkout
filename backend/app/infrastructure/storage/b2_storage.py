import os
import boto3
import logging
from typing import Optional
from botocore.config import Config
from botocore.exceptions import ClientError, BotoCoreError
from app.core.config import settings

logger = logging.getLogger(__name__)


class BackblazeB2Storage:
    """
    Backblaze B2 Object Storage (S3-compatible).
    Free allowance: 10GB storage, 3x egress.
    Configured with S3v4 signature and automatic local storage fallback.
    """

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        key_id: Optional[str] = None,
        app_key: Optional[str] = None,
        bucket_name: str = "checkout123456789876543",
        local_dir: str = "/tmp/checkout_storage"
    ):
        self.bucket_name = bucket_name
        self.local_dir = local_dir
        self.has_b2 = bool(endpoint_url and key_id and app_key)
        self.s3_client = None

        os.makedirs(self.local_dir, exist_ok=True)

        if self.has_b2:
            try:
                b2_config = Config(
                    signature_version="s3v4",
                    connect_timeout=15,
                    read_timeout=30,
                    retries={"max_attempts": 3, "mode": "standard"}
                )
                self.s3_client = boto3.client(
                    "s3",
                    endpoint_url=endpoint_url,
                    aws_access_key_id=key_id,
                    aws_secret_access_key=app_key,
                    config=b2_config
                )
            except Exception as e:
                logger.warning(f"Failed to initialize B2 client: {e}. Using local storage fallback.")
                self.has_b2 = False

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
            except Exception as e:
                logger.warning(f"Backblaze B2 upload error ({type(e).__name__}: {e}). Using local storage fallback.")

        # Local fallback
        try:
            path = os.path.join(self.local_dir, file_name)
            with open(path, "wb") as f:
                f.write(file_bytes)
            return f"file://{path}"
        except Exception as e:
            logger.error(f"Local file fallback write failed: {e}")
            return f"local://{file_name}"

    def download_file(self, file_name: str) -> bytes:
        if self.has_b2 and self.s3_client:
            try:
                obj = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_name)
                return obj["Body"].read()
            except Exception as e:
                logger.warning(f"Backblaze B2 download error ({type(e).__name__}: {e}). Falling back to local storage.")

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
