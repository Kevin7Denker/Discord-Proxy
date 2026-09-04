import unittest

from core.connection_classifier import ConnectionCategory
from core.local_relay import LocalRelayService
from core.network_service import ProxyEndpoint


class LocalRelayObservabilityTests(unittest.TestCase):
    def test_connect_event_classifies_socks_tcp_destination(self):
        relay = LocalRelayService(ProxyEndpoint("proxy.example", 1080, "SOCKS5"))

        event = relay._build_connect_event(
            connection_id="conn:000123",
            host="gateway.discord.gg",
            port=443,
            protocol="TCP",
            transport="SOCKS_TCP",
            result="connected",
            latency_ms=15,
        )

        self.assertEqual(ConnectionCategory.GATEWAY, event.category)
        self.assertEqual("gateway.discord.gg", event.destination_hostname)
        self.assertEqual(443, event.destination_port)
        self.assertEqual("TCP", event.protocol)
        self.assertEqual("SOCKS_TCP", event.transport)


if __name__ == "__main__":
    unittest.main()
