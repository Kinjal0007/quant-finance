from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pandas as pd

try:
    from google.cloud import storage

    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    print("Warning: google-cloud-storage not available. GCS functionality disabled.")


class GCSWriter:
    """Google Cloud Storage writer for job artifacts."""

    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT")
        self.bucket_name = os.getenv("QFP_ARTIFACTS_BUCKET")

        if not self.project_id:
            raise ValueError("GCP_PROJECT environment variable is required")

        if not self.bucket_name:
            raise ValueError("QFP_ARTIFACTS_BUCKET environment variable is required")

        if GCS_AVAILABLE:
            self.client = storage.Client(project=self.project_id)
            self.bucket = self.client.bucket(self.bucket_name)
        else:
            self.client = None
            self.bucket = None

    def write_metrics_json(
        self, job_id: str, metrics: Dict[str, Any], filename: str = "metrics.json"
    ) -> str:
        """
        Write metrics to GCS as JSON.

        Args:
            job_id: Job identifier
            metrics: Metrics dictionary
            filename: Output filename

        Returns:
            GCS object path
        """
        if not self.bucket:
            raise RuntimeError("GCS client not available")

        # Create job directory path
        job_path = f"jobs/{job_id}/{filename}"

        # Convert metrics to JSON string
        metrics_json = json.dumps(metrics, indent=2, default=str)

        # Write to GCS
        blob = self.bucket.blob(job_path)
        blob.upload_from_string(metrics_json, content_type="application/json")

        print(f"Wrote metrics to gs://{self.bucket_name}/{job_path}")
        return job_path

    def write_artifact_csv(self, job_id: str, df: pd.DataFrame, filename: str) -> str:
        """
        Write DataFrame to GCS as CSV.

        Args:
            job_id: Job identifier
            df: DataFrame to write
            filename: Output filename

        Returns:
            GCS object path
        """
        if not self.bucket:
            raise RuntimeError("GCS client not available")

        # Create job directory path
        job_path = f"jobs/{job_id}/{filename}"

        # Convert DataFrame to CSV string
        csv_string = df.to_csv(index=True)

        # Write to GCS
        blob = self.bucket.blob(job_path)
        blob.upload_from_string(csv_string, content_type="text/csv")

        print(f"Wrote CSV to gs://{self.bucket_name}/{job_path}")
        return job_path

    def write_artifact_parquet(
        self, job_id: str, df: pd.DataFrame, filename: str
    ) -> str:
        """
        Write DataFrame to GCS as Parquet.

        Args:
            job_id: Job identifier
            df: DataFrame to write
            filename: Output filename

        Returns:
            GCS object path
        """
        if not self.bucket:
            raise RuntimeError("GCS client not available")

        # Create job directory path
        job_path = f"jobs/{job_id}/{filename}"

        # Convert DataFrame to Parquet bytes
        parquet_bytes = df.to_parquet(index=True)

        # Write to GCS
        blob = self.bucket.blob(job_path)
        blob.upload_from_string(parquet_bytes, content_type="application/octet-stream")

        print(f"Wrote Parquet to gs://{self.bucket_name}/{job_path}")
        return job_path

    def write_artifact_dataframe(
        self, job_id: str, df: pd.DataFrame, name: str, format: str = "csv"
    ) -> str:
        """
        Write DataFrame to GCS in specified format.

        Args:
            job_id: Job identifier
            df: DataFrame to write
            name: Artifact name
            format: Output format (csv, parquet)

        Returns:
            GCS object path
        """
        if format.lower() == "csv":
            filename = f"{name}.csv"
            return self.write_artifact_csv(job_id, df, filename)
        elif format.lower() == "parquet":
            filename = f"{name}.parquet"
            return self.write_artifact_parquet(job_id, df, filename)
        else:
            raise ValueError("Format must be 'csv' or 'parquet'")

    def generate_signed_urls(
        self, job_id: str, expiration_minutes: int = 10
    ) -> List[str]:
        """
        Generate signed URLs for job artifacts.

        Args:
            job_id: Job identifier
            expiration_minutes: URL expiration time in minutes

        Returns:
            List of signed URLs
        """
        if not self.bucket:
            raise RuntimeError("GCS client not available")

        # List all objects in job directory
        job_prefix = f"jobs/{job_id}/"
        blobs = self.client.list_blobs(self.bucket, prefix=job_prefix)

        signed_urls = []
        expiration = timedelta(minutes=expiration_minutes)

        for blob in blobs:
            # Generate signed URL
            url = blob.generate_signed_url(
                version="v4", expiration=expiration, method="GET"
            )
            signed_urls.append(url)

        return signed_urls

    def get_job_artifacts(self, job_id: str) -> List[Dict[str, str]]:
        """
        Get list of artifacts for a job.

        Args:
            job_id: Job identifier

        Returns:
            List of artifact information
        """
        if not self.bucket:
            raise RuntimeError("GCS client not available")

        # List all objects in job directory
        job_prefix = f"jobs/{job_id}/"
        blobs = self.client.list_blobs(self.bucket, prefix=job_prefix)

        artifacts = []
        for blob in blobs:
            # Extract filename from full path
            filename = blob.name.replace(job_prefix, "")

            artifacts.append(
                {
                    "name": filename,
                    "size": blob.size,
                    "created": (
                        blob.time_created.isoformat() if blob.time_created else None
                    ),
                    "content_type": blob.content_type,
                }
            )

        return artifacts

    def delete_job_artifacts(self, job_id: str) -> bool:
        """
        Delete all artifacts for a job.

        Args:
            job_id: Job identifier

        Returns:
            True if successful
        """
        if not self.bucket:
            raise RuntimeError("GCS client not available")

        try:
            # List all objects in job directory
            job_prefix = f"jobs/{job_id}/"
            blobs = self.client.list_blobs(self.bucket, prefix=job_prefix)

            # Delete each blob
            for blob in blobs:
                blob.delete()

            print(f"Deleted artifacts for job {job_id}")
            return True

        except Exception as e:
            print(f"Error deleting artifacts for job {job_id}: {e}")
            return False

    def write_job_summary(
        self,
        job_id: str,
        job_type: str,
        symbols: List[str],
        start_date: str,
        end_date: str,
        metrics: Dict[str, Any],
        artifacts: List[str],
    ) -> str:
        """
        Write job summary to GCS.

        Args:
            job_id: Job identifier
            job_type: Type of job
            symbols: List of symbols analyzed
            start_date: Start date
            end_date: End date
            metrics: Job metrics
            artifacts: List of artifact paths

        Returns:
            GCS object path
        """
        summary = {
            "job_id": job_id,
            "job_type": job_type,
            "symbols": symbols,
            "start_date": start_date,
            "end_date": end_date,
            "created_at": datetime.utcnow().isoformat(),
            "metrics": metrics,
            "artifacts": artifacts,
        }

        return self.write_metrics_json(job_id, summary, "summary.json")


# Global GCS writer instance
gcs_writer = GCSWriter()


def get_gcs_writer() -> GCSWriter:
    """Get GCS writer instance."""
    return gcs_writer
