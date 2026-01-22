#!/usr/bin/env python3
import json
import uuid
import pika
from pika.exchange_type import ExchangeType
from pydantic import BaseModel

connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost")) # type: ignore
channel = connection.channel()

EXCHANGE = "certification"
ROUTING_KEY = "certification"


class CertificatePayload(BaseModel):
    name: str
    certificate_name: str
    clean: str
    membership_id: str
    certificate_id: str

user = CertificatePayload(
    name="Fidelugwuowo Dilibe",
    certificate_name="Working man",
    clean="lafuging",
    membership_id="130932",
    certificate_id="1234223",
)

task_id = str(uuid.uuid4())
kwargs = user.model_dump(exclude_unset=True)

body = json.dumps(
    [
        [],    
        kwargs,
        {}     
    ]
).encode("utf-8", "ignore")

headers = {
    "lang": "py",
    "task": "certification.first_tasks",
    "id": task_id,
    "retries": 5,
    "timelimit": [30000, None],
    "origin": "pika-producer",
}

channel.basic_publish(
    exchange=EXCHANGE,
    routing_key=ROUTING_KEY,
    body=body,
    properties=pika.BasicProperties(
        content_type="application/json",
        content_encoding="utf-8",
        headers=headers,
        delivery_mode=2,
    ),
)

print("✅ Sent task:", task_id)
connection.close()