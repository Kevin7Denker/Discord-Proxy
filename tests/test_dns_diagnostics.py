import socket
import unittest

from core.dns_diagnostics import DnsResult, classify_dns_error


class DnsDiagnosticsTests(unittest.TestCase):
    def test_classifies_nxdomain_without_treating_as_critical_transport_failure(self):
        error = socket.gaierror(socket.EAI_NONAME, "Name or service not known")

        self.assertEqual(DnsResult.NXDOMAIN, classify_dns_error(error))

    def test_classifies_timeout(self):
        self.assertEqual(DnsResult.TIMEOUT, classify_dns_error(TimeoutError("timed out")))

    def test_classifies_network_unavailable(self):
        self.assertEqual(DnsResult.NETWORK_UNAVAILABLE, classify_dns_error(OSError(101, "Network is unreachable")))


if __name__ == "__main__":
    unittest.main()
