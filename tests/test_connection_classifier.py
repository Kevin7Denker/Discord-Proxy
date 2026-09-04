import unittest

from core.connection_classifier import ConnectionCategory, classify_connection


class ConnectionClassifierTests(unittest.TestCase):
    def test_classifies_gateway_by_hostname(self):
        result = classify_connection("gateway.discord.gg", None, 443, "TCP")

        self.assertEqual(ConnectionCategory.GATEWAY, result.category)
        self.assertEqual("hostname", result.reason)

    def test_classifies_media_by_hostname_without_fixed_ip(self):
        result = classify_connection("latency.discord.media", "162.159.130.234", 443, "TCP")

        self.assertEqual(ConnectionCategory.MEDIA, result.category)
        self.assertEqual("hostname", result.reason)

    def test_does_not_classify_cloudflare_ip_without_hostname(self):
        result = classify_connection(None, "162.159.130.234", 443, "UDP")

        self.assertEqual(ConnectionCategory.UNKNOWN, result.category)
        self.assertEqual("fallback", result.reason)


if __name__ == "__main__":
    unittest.main()
