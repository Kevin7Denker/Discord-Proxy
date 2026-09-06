import unittest

from core.connection_classifier import ConnectionCategory
from core.observability import ConnectionEvent
from core.screen_share_diagnostics import ScreenShareDiagnostics


class ScreenShareDiagnosticsTests(unittest.TestCase):
    def test_builds_summary_when_receiver_timeout_occurs(self):
        diagnostics = ScreenShareDiagnostics()

        diagnostics.record(
            ConnectionEvent(
                connection_id="conn:000021",
                process="Discord",
                destination_hostname="c-ewr13-b24de978.discord.media",
                destination_port=2087,
                protocol="TCP",
                transport="RTC_CONTROL_WEBSOCKET",
                category=ConnectionCategory.SCREEN_SHARE,
                result="rtc_control_connected",
                metadata={"media_context": "stream"},
            )
        )
        diagnostics.record(
            ConnectionEvent(
                connection_id="conn:000025",
                process="Discord",
                destination_ip="104.29.156.113",
                destination_port=19322,
                protocol="UDP",
                transport="DIRECT_UDP",
                category=ConnectionCategory.SCREEN_SHARE,
                result="rtc_media_server_connected",
                metadata={"media_context": "stream", "address_role": "remote"},
            )
        )

        summary = diagnostics.record(
            ConnectionEvent(
                connection_id="conn:000028",
                process="Discord",
                protocol="RTC",
                transport="DISCORD_MEDIA_ENGINE",
                category=ConnectionCategory.SCREEN_SHARE,
                result="video-stream-receiver-ready-timeout",
                error="video-stream-receiver-ready-timeout",
                metadata={"media_context": "stream"},
            )
        )

        self.assertIsNotNone(summary)
        self.assertEqual("screen_share_diagnostic", summary.result)
        self.assertEqual(ConnectionCategory.SCREEN_SHARE, summary.category)
        self.assertEqual("c-ewr13-b24de978.discord.media:2087", summary.metadata["rtc_control_endpoint"])
        self.assertEqual("104.29.156.113:19322", summary.metadata["media_server_endpoint"])
        self.assertEqual("video-stream-receiver-ready-timeout", summary.metadata["failure"])

    def test_ignores_voice_timeouts(self):
        diagnostics = ScreenShareDiagnostics()

        summary = diagnostics.record(
            ConnectionEvent(
                connection_id="conn:000099",
                process="Discord",
                protocol="RTC",
                transport="DISCORD_MEDIA_ENGINE",
                category=ConnectionCategory.VOICE,
                result="video-stream-receiver-ready-timeout",
                metadata={"media_context": "default"},
            )
        )

        self.assertIsNone(summary)


if __name__ == "__main__":
    unittest.main()
