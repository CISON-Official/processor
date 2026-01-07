#!/usr/bin/env python3
import json

import pika
from pika.exchange_type import ExchangeType
from pydantic import BaseModel

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="localhost") # type: ignore
)
channel = connection.channel()



QUEUE_NAME = "2025_certification"
EXCHANGE_NAME = "certification"
ROUTING_KEY = "certification"

queue_arguments = {
    "x-dead-letter-exchange": "dlx",
    "x-dead-letter-routing-key": "dead",
    "x-message-ttl": 600_000,  # 10 minutes
}

channel.exchange_declare(
    exchange=EXCHANGE_NAME,
    exchange_type=ExchangeType.direct,
    durable=True,
)

channel.queue_declare(
    queue=QUEUE_NAME,
    durable=True,
    arguments=queue_arguments,
)

channel.queue_bind(
    queue=QUEUE_NAME,
    exchange=EXCHANGE_NAME,
    routing_key=ROUTING_KEY,
)


class CertificatePayload(BaseModel):
    name: str
    certificate_name: str


user = CertificatePayload(
    name="Fidelugwuowo Dilibe",
    certificate_name="Working man",
)

body = json.dumps(user.model_dump()).encode("utf-8")

channel.basic_publish(
    exchange=EXCHANGE_NAME,
    routing_key=ROUTING_KEY,
    body=body,
    properties=pika.BasicProperties(
        content_type="application/json",
        delivery_mode=2,  # persistent
    ),
)

print("✅ Message published")

connection.close()
