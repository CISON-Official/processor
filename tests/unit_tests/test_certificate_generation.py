#!/usr/bin/env python3

import json
import uuid
import unittest
from unittest.mock import MagicMock, patch

from tests.preset import CertificatePayload, CertificatePublisher


class TestCertificatePayload(unittest.TestCase):
    """Unit tests for the CertificatePayload model"""
    
    def test_valid_payload_creation(self):
        """Test creating a valid payload"""
        payload = CertificatePayload(
            name="John Doe",
            certificate_name="Python Expert",
            clean="test"
        )
        self.assertEqual(payload.name, "John Doe")
        self.assertEqual(payload.certificate_name, "Python Expert")
        self.assertEqual(payload.clean, "test")
    
    def test_payload_model_dump(self):
        """Test payload serialization"""
        payload = CertificatePayload(
            name="Jane Smith",
            certificate_name="Data Scientist",
            clean="verified"
        )
        data = payload.model_dump()
        self.assertIsInstance(data, dict)
        self.assertIn("name", data)
        self.assertIn("certificate_name", data)
        self.assertIn("clean", data)


class TestCertificatePublisherUnit(unittest.TestCase):
    """Unit tests for CertificatePublisher (mocked)"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.publisher = CertificatePublisher(host="localhost")
        self.test_payload = CertificatePayload(
            name="Test User",
            certificate_name="Test Certificate",
            clean="test_clean"
        )
    
    @patch('pika.BlockingConnection')
    def test_connect(self, mock_connection_class):
        """Test connection establishment"""
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_connection_class.return_value = mock_connection
        
        self.publisher.connect()
        
        mock_connection_class.assert_called_once()
        self.assertIsNotNone(self.publisher.connection)
        self.assertIsNotNone(self.publisher.channel)
    
    @patch('pika.BlockingConnection')
    def test_publish_certificate_task(self, mock_connection_class):
        """Test publishing a certificate task"""
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_connection_class.return_value = mock_connection
        
        self.publisher.connect()
        task_id = self.publisher.publish_certificate_task(self.test_payload)
        
        # Verify basic_publish was called
        mock_channel.basic_publish.assert_called_once()
        
        # Verify task_id is a valid UUID
        self.assertIsInstance(task_id, str)
        uuid.UUID(task_id)  # This will raise if invalid
    
    @patch('pika.BlockingConnection')
    def test_publish_with_custom_task_id(self, mock_connection_class):
        """Test publishing with a custom task ID"""
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_connection_class.return_value = mock_connection
        
        custom_id = str(uuid.uuid4())
        self.publisher.connect()
        task_id = self.publisher.publish_certificate_task(
            self.test_payload, 
            task_id=custom_id
        )
        
        self.assertEqual(task_id, custom_id)
    
    @patch('pika.BlockingConnection')
    def test_message_body_format(self, mock_connection_class):
        """Test that message body has correct format"""
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_connection_class.return_value = mock_connection
        
        self.publisher.connect()
        self.publisher.publish_certificate_task(self.test_payload)
        
        # Get the call arguments
        call_args = mock_channel.basic_publish.call_args
        body = call_args[1]['body']
        
        # Decode and parse the body
        decoded_body = json.loads(body.decode('utf-8'))
        
        # Verify format: [args, kwargs, embed]
        self.assertIsInstance(decoded_body, list)
        self.assertEqual(len(decoded_body), 3)
        self.assertEqual(decoded_body[0], [])  # args
        self.assertIsInstance(decoded_body[1], dict)  # kwargs
        self.assertEqual(decoded_body[2], {})  # embed
        
        # Verify payload content
        self.assertEqual(decoded_body[1]['name'], "Test User")
        self.assertEqual(decoded_body[1]['certificate_name'], "Test Certificate")
    
    @patch('pika.BlockingConnection')
    def test_message_headers(self, mock_connection_class):
        """Test that message headers are correct"""
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_connection_class.return_value = mock_connection
        
        self.publisher.connect()
        custom_id = str(uuid.uuid4())
        self.publisher.publish_certificate_task(self.test_payload, task_id=custom_id)
        
        # Get the properties argument
        call_args = mock_channel.basic_publish.call_args
        properties = call_args[1]['properties']
        
        self.assertEqual(properties.content_type, "application/json")
        self.assertEqual(properties.content_encoding, "utf-8")
        self.assertEqual(properties.delivery_mode, 2)
        self.assertEqual(properties.headers['task'], "certification.first_tasks")
        self.assertEqual(properties.headers['id'], custom_id)
        self.assertEqual(properties.headers['retries'], 5)
    
    def test_publish_without_connection_raises_error(self):
        """Test that publishing without connection raises error"""
        with self.assertRaises(RuntimeError):
            self.publisher.publish_certificate_task(self.test_payload)
    
    @patch('pika.BlockingConnection')
    def test_close_connection(self, mock_connection_class):
        """Test closing the connection"""
        mock_connection = MagicMock()
        mock_connection.is_closed = False
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_connection_class.return_value = mock_connection
        
        self.publisher.connect()
        self.publisher.close()
        
        mock_connection.close.assert_called_once()
