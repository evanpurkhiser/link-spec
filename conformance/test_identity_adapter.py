#!/usr/bin/env python3

import hashlib
from ipaddress import IPv4Address
from pathlib import Path
from unittest import TestCase, main

from identity_adapter import (
    keepalive,
    load_status_packet,
    parse_mac,
    player_status,
)


CAPTURED_CDJ_3000 = (
    "5173707431576d4a4f4c060043444a2d33303030000000000000000000000000"
    "0103003601012497ed0b4043c0a80198030000000164"
)

CAPTURED_XDJ_RX3 = (
    "5173707431576d4a4f4c060058444a2d52583300000000000000000000000000"
    "010300360b0274da382b2d450a00008f010000000700"
)

CAPTURED_XDJ_RX3_STATUS_PLAYER_11 = (
    "5173707431576d4a4f4c0a58444a2d5258330000000000000000000000000001050b01000b0001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000400000000000000000000000000000000000000000080009e001000007fffffff8000ffff00000000000000ffffffffff01ff00000000000000000000000000000000010000000000000000000000000000000000000000001f010000123456780000000101010101010100000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
)


class IdentityAdapterTest(TestCase):
    def test_reproduces_captured_cdj_3000_keepalive(self) -> None:
        packet = keepalive(
            model="CDJ-3000",
            player=1,
            device_type=1,
            mac=parse_mac("24:97:ed:0b:40:43"),
            address=IPv4Address("192.168.1.152"),
            peers=3,
            generation=3,
        )
        self.assertEqual(packet.hex(), CAPTURED_CDJ_3000)

    def test_rejects_names_that_do_not_fit_the_wire_field(self) -> None:
        with self.assertRaises(ValueError):
            keepalive(
                model="x" * 21,
                player=1,
                device_type=1,
                mac=parse_mac("02:00:00:60:00:01"),
                address=IPv4Address("172.31.96.50"),
                peers=0,
                generation=3,
            )

    def test_reproduces_captured_xdj_rx3_keepalive(self) -> None:
        packet = keepalive(
            model="XDJ-RX3",
            player=11,
            device_type=7,
            mac=parse_mac("74:da:38:2b:2d:45"),
            address=IPv4Address("10.0.0.143"),
            peers=1,
            generation=3,
            presence=2,
            model_code=0,
        )
        self.assertEqual(packet.hex(), CAPTURED_XDJ_RX3)

    def test_reproduces_captured_xdj_rx3_player_status(self) -> None:
        packet = player_status(model="XDJ-RX3", player=11)
        self.assertEqual(packet.hex(), CAPTURED_XDJ_RX3_STATUS_PLAYER_11)

    def test_player_status_patches_both_device_number_fields(self) -> None:
        packet = player_status(model="XDJ-AZ", player=4)
        self.assertEqual(packet[0x0A], 0x0A)
        self.assertEqual(packet[0x0B:0x1F], b"XDJ-AZ".ljust(20, b"\0"))
        self.assertEqual(packet[0x21], 4)
        self.assertEqual(packet[0x24], 4)

    def test_loads_captured_cdj_2000nexus_status_without_mutation(self) -> None:
        packet = load_status_packet(
            Path("status-packets/cdj-2000nexus-player-1.hex"),
            model="CDJ-2000nexus",
            player=1,
        )

        self.assertEqual(
            "8e9c36049a85be2f31c989bfbff415d989bdb0f395987135eb35f53f1d8fb70b",
            hashlib.sha256(packet).hexdigest(),
        )

    def test_loads_corroborating_xdj_xz_status_without_mutation(self) -> None:
        packet = load_status_packet(
            Path("status-packets/xdj-xz-player-1-analyzed-status-20260422.hex"),
            model="XDJ-XZ",
            player=1,
        )

        self.assertEqual(292, len(packet))
        self.assertEqual(
            "8eadeb284e6c0ed167cd1573ba0ed976d5c1abd85694de1299224b54519ff90f",
            hashlib.sha256(packet).hexdigest(),
        )

    def test_rejects_status_packet_identity_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not match"):
            load_status_packet(
                Path("status-packets/cdj-2000nexus-player-1.hex"),
                model="CDJ-3000",
                player=1,
            )


if __name__ == "__main__":
    main()
