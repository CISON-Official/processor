#!/usr/bin/env python3


# Your application code (refactored for testability)
import json
import uuid
import pika
from pydantic import BaseModel


class CertificatePayload(BaseModel):
    name: str
    certificate_name: str
    clean: str


class CertificatePublisher:
    EXCHANGE = "certification"
    ROUTING_KEY = "certification"

    def __init__(self, host="localhost"):
        self.host = host
        self.connection = None
        self.channel = None

    def connect(self):
        """Establish connection to RabbitMQ"""
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host)  # type: ignore
        )
        self.channel = self.connection.channel()

    def publish_certificate_task(self, payload: CertificatePayload, task_id: str = ""):
        """Publish a certificate generation task"""
        if not self.channel:
            raise RuntimeError("Not connected. Call connect() first.")

        task_id = task_id or str(uuid.uuid4())
        kwargs = payload.model_dump(exclude_unset=True)

        body = json.dumps([[], kwargs, {}]).encode("utf-8", "ignore")

        headers = {
            "lang": "py",
            "task": "certification.first_tasks",
            "id": task_id,
            "retries": 5,
            "timelimit": [30000, None],
            "origin": "pika-producer",
        }

        self.channel.basic_publish(
            exchange=self.EXCHANGE,
            routing_key=self.ROUTING_KEY,
            body=body,
            properties=pika.BasicProperties(
                content_type="application/json",
                content_encoding="utf-8",
                headers=headers,
                delivery_mode=2,
            ),
        )

        return task_id

    def close(self):
        """Close the connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            self.connection = None
            self.channel = None
