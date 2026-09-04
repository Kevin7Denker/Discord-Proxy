import json
import tempfile
import unittest
from pathlib import Path

from core.connection_classifier import ConnectionCategory
from core.observability import (
    ConnectionEvent,
    ConnectionObserver,
    LogLevel,
    detect_ip_version,
    next_connection_id,
)


class FakeLogger:
    def __init__(self):
        self.messages = []

    def info(self, message):
        self.messages.append(("INFO", message))

    def warning(self, message):
        self.messages.append(("WARN", message))

    def error(self, message):
        self.messages.append(("ERROR", message))

    def debug(self, message):
        self.messages.append(("DEBUG", message))


class ObservabilityTests(unittest.TestCase):
    def test_detects_ip_version(self):
        self.assertEqual("IPv4", detect_ip_version("162.159.130.234"))
        self.assertEqual("IPv6", detect_ip_version("fd12::10"))
        self.assertIsNone(detect_ip_version("discord.com"))

    def test_event_serializes_required_fields(self):
        event = ConnectionEvent(
            connection_id=next_connection_id(),
            process="Discord",
            destination_hostname="gateway.discord.gg",
            destination_ip="162.159.135.234",
            destination_port=443,
            protocol="TCP",
            transport="SOCKS_TCP",
            category=ConnectionCategory.GATEWAY,
            result="connected",
            latency_ms=42,
            metadata={"stage": "gateway"},
        )

        payload = event.to_dict()

        self.assertTrue(payload["connection_id"].startswith("conn:"))
        self.assertEqual("IPv4", payload["ip_version"])
        self.assertEqual("GATEWAY", payload["category"])
        self.assertEqual("SOCKS_TCP", payload["transport"])
        self.assertEqual({"stage": "gateway"}, payload["metadata"])

    def test_observer_logs_compact_line_and_jsonl(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sink = Path(temp_dir) / "connections.jsonl"
            logger = FakeLogger()
            observer = ConnectionObserver(logger=logger, level=LogLevel.INFO, sink_path=sink)

            observer.emit(
                ConnectionEvent(
                    connection_id="conn:000001",
                    process="Discord",
                    destination_hostname="discord.com",
                    destination_port=443,
                    protocol="TCP",
                    transport="SOCKS_TCP",
                    category=ConnectionCategory.API,
                    result="connected",
                )
            )

            self.assertEqual(1, len(logger.messages))
            self.assertIn("[conn:000001]", logger.messages[0][1])
            self.assertIn("category=API", logger.messages[0][1])
            saved = json.loads(sink.read_text(encoding="utf-8").strip())
            self.assertEqual("conn:000001", saved["connection_id"])
            self.assertEqual("discord.com", saved["destination_hostname"])


if __name__ == "__main__":
    unittest.main()
