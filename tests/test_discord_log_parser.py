import unittest

from core.connection_classifier import ConnectionCategory
from core.discord_log_parser import parse_discord_log_line


class DiscordLogParserTests(unittest.TestCase):
    def test_parses_stream_rtc_control_connect(self):
        event = parse_discord_log_line(
            "14:58:01.514 > [RTCControlSocket(stream)] [CONNECT] wss://c-ewr11-eb153ce8.discord.media:443/"
        )

        self.assertIsNotNone(event)
        self.assertEqual(ConnectionCategory.SCREEN_SHARE, event.category)
        self.assertEqual("TCP", event.protocol)
        self.assertEqual("RTC_CONTROL_WEBSOCKET", event.transport)
        self.assertEqual("c-ewr11-eb153ce8.discord.media", event.destination_hostname)
        self.assertEqual(443, event.destination_port)
        self.assertEqual("rtc_control_connect", event.result)
        self.assertEqual("stream", event.metadata["media_context"])

    def test_parses_udp_media_connection(self):
        event = parse_discord_log_line(
            "14:58:02.950 > [Connection(stream)] Connected with local address 45.179.29.128:13236 and protocol: udp"
        )

        self.assertIsNotNone(event)
        self.assertEqual(ConnectionCategory.SCREEN_SHARE, event.category)
        self.assertEqual("UDP", event.protocol)
        self.assertEqual("DIRECT_UDP", event.transport)
        self.assertEqual("45.179.29.128", event.destination_ip)
        self.assertEqual(13236, event.destination_port)
        self.assertEqual("media_connected", event.result)

    def test_parses_media_server_destination(self):
        event = parse_discord_log_line(
            "14:58:02.958 > [RTCConnection(1545493147713405060, stream)] RTC connected to media server: 104.29.156.169:19294"
        )

        self.assertIsNotNone(event)
        self.assertEqual(ConnectionCategory.SCREEN_SHARE, event.category)
        self.assertEqual("UDP", event.protocol)
        self.assertEqual("DIRECT_UDP", event.transport)
        self.assertEqual("104.29.156.169", event.destination_ip)
        self.assertEqual(19294, event.destination_port)
        self.assertEqual("rtc_media_server_connected", event.result)

    def test_parses_stream_receiver_timeout_as_2012_candidate(self):
        event = parse_discord_log_line(
            '14:58:23.233 > [AVError] AV error reported: video-stream-receiver-ready-timeout {"videoStreamId":"6","mediaContext":"stream"}'
        )

        self.assertIsNotNone(event)
        self.assertEqual(ConnectionCategory.SCREEN_SHARE, event.category)
        self.assertEqual("RTC", event.protocol)
        self.assertEqual("DISCORD_MEDIA_ENGINE", event.transport)
        self.assertEqual("video-stream-receiver-ready-timeout", event.result)
        self.assertEqual("stream", event.metadata["media_context"])


if __name__ == "__main__":
    unittest.main()
