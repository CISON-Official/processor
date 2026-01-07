import unittest

from tests.integrated_tests.tests_certificate_generation import (
    TestCertificatePublisherIntegration,
)
from tests.unit_tests.test_certificate_generation import (
    TestCertificatePayload,
    TestCertificatePublisherUnit,
)


if __name__ == "__main__":
    # Run unit tests
    print("=" * 70)
    print("RUNNING UNIT TESTS")
    print("=" * 70)
    unit_suite = unittest.TestLoader().loadTestsFromTestCase(TestCertificatePayload)
    unit_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestCertificatePublisherUnit)
    )
    unittest.TextTestRunner(verbosity=2).run(unit_suite)

    # Run integration tests
    print("\n" + "=" * 70)
    print("RUNNING INTEGRATION TESTS (requires RabbitMQ)")
    print("=" * 70)
    integration_suite = unittest.TestLoader().loadTestsFromTestCase(
        TestCertificatePublisherIntegration
    )
    unittest.TextTestRunner(verbosity=2).run(integration_suite)
