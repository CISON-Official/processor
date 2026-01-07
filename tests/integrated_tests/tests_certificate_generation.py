#!/usr/bin/env python3


import uuid
import unittest

import pika

from tests.preset import CertificatePayload, CertificatePublisher


class TestCertificatePublisherIntegration(unittest.TestCase):
    """Integration tests for CertificatePublisher (requires RabbitMQ)"""

    @classmethod
    def setUpClass(cls):
        """Check if RabbitMQ is available"""
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host="localhost")  # type: ignore
            )
            connection.close()
            cls.rabbitmq_available = True
        except Exception:
            cls.rabbitmq_available = False

    def setUp(self):
        """Set up test fixtures"""
        if not self.rabbitmq_available:
            self.skipTest("RabbitMQ not available")

        self.publisher = CertificatePublisher(host="localhost")
        self.test_payload = CertificatePayload(
            name="Integration Test User",
            certificate_name="Integration Test Certificate",
            clean="integration_test",
        )

    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self, "publisher"):
            self.publisher.close()

    def test_end_to_end_publish(self):
        """Test actual publishing to RabbitMQ"""
        self.publisher.connect()
        task_id = self.publisher.publish_certificate_task(self.test_payload)

        # Verify task_id is valid
        self.assertIsInstance(task_id, str)
        uuid.UUID(task_id)

        print(f"✅ Published task: {task_id}")

    def test_multiple_publishes(self):
        """Test publishing multiple tasks"""
        self.publisher.connect()

        task_ids = []
        for i in range(3):
            payload = CertificatePayload(
                name=f"User {i}", certificate_name=f"Certificate {i}", clean=f"test_{i}"
            )
            task_id = self.publisher.publish_certificate_task(payload)
            task_ids.append(task_id)

        # Verify all task_ids are unique
        self.assertEqual(len(task_ids), len(set(task_ids)))
        print(f"✅ Published {len(task_ids)} tasks")

    def test_connection_and_reconnection(self):
        """Test connecting, closing, and reconnecting"""
        # First connection
        self.publisher.connect()
        task_id_1 = self.publisher.publish_certificate_task(self.test_payload)
        self.publisher.close()

        # Reconnection
        self.publisher.connect()
        task_id_2 = self.publisher.publish_certificate_task(self.test_payload)

        # Verify both succeeded and are different
        self.assertIsInstance(task_id_1, str)
        self.assertIsInstance(task_id_2, str)
        self.assertNotEqual(task_id_1, task_id_2)
