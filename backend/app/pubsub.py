from __future__ import annotations

import json
import os
from typing import Any, Dict

try:
    from google.cloud import pubsub_v1
    PUBSUB_AVAILABLE = True
except ImportError:
    PUBSUB_AVAILABLE = False
    print("Warning: google-cloud-pubsub not available. Pub/Sub functionality disabled.")


class PubSubPublisher:
    """Publisher for Google Cloud Pub/Sub messages."""
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT")
        self.topic_id = os.getenv("PUBSUB_TOPIC", "jobs")
        self.publisher = None
        self.topic_path = None
        
        # Only initialize if we have the required environment variables
        if self.project_id and PUBSUB_AVAILABLE:
            try:
                self.publisher = pubsub_v1.PublisherClient()
                self.topic_path = self.publisher.topic_path(self.project_id, self.topic_id)
                print(f"Pub/Sub initialized for topic: {self.topic_path}")
            except Exception as e:
                print(f"Warning: Failed to initialize Pub/Sub: {e}")
                print("Pub/Sub functionality will be disabled")
                self.publisher = None
                self.topic_path = None
        else:
            if not self.project_id:
                print("Warning: GCP_PROJECT not set, Pub/Sub disabled")
            if not PUBSUB_AVAILABLE:
                print("Warning: google-cloud-pubsub not available, Pub/Sub disabled")
    
    def publish_job(self, job_data: Dict[str, Any]) -> str:
        """
        Publish a job message to Pub/Sub.
        
        Args:
            job_data: Job data to publish
            
        Returns:
            Message ID if successful, None if Pub/Sub unavailable
        """
        if not self.publisher:
            print(f"Warning: Pub/Sub not available. Would publish: {job_data}")
            return None
        
        try:
            # Convert job data to JSON string
            message_data = json.dumps(job_data, default=str).encode("utf-8")
            
            # Publish message
            future = self.publisher.publish(self.topic_path, data=message_data)
            message_id = future.result()
            
            print(f"Published job message: {message_id}")
            return message_id
            
        except Exception as e:
            print(f"Error publishing job message: {e}")
            raise
    
    def publish_job_created(self, job_id: str, job_type: str, **kwargs) -> str:
        """
        Publish a job created message.
        
        Args:
            job_id: Job identifier
            job_type: Type of job
            **kwargs: Additional job data
            
        Returns:
            Message ID
        """
        message_data = {
            "event_type": "job_created",
            "job_id": job_id,
            "job_type": job_type,
            **kwargs
        }
        
        return self.publish_job(message_data)


# Global publisher instance - initialize lazily
_pubsub_publisher = None


def get_pubsub_publisher() -> PubSubPublisher:
    """Get Pub/Sub publisher instance."""
    global _pubsub_publisher
    if _pubsub_publisher is None:
        _pubsub_publisher = PubSubPublisher()
    return _pubsub_publisher
