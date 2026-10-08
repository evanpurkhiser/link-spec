import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ARTIFACT = ROOT / "data/static-analysis/song-info-command-lifecycle.disasm.txt"
CONNECTION = ROOT / "data/static-analysis/dbserver-connection-send.disasm.txt"
DISPATCH = ROOT / "data/static-analysis/display-song-info-dispatch.disasm.txt"
BUILDERS = ROOT / "data/static-analysis/song-info-siblings.disasm.txt"
BINARY = (
    ROOT.parent
    / "artifacts/rekordbox/7.2.19/extracted/app-root/rekordbox.app"
    / "Contents/MacOS/rekordbox"
)


class SongInfoCommandLifecycleTests(unittest.TestCase):
    def test_artifact_and_binary_are_pinned(self) -> None:
        self.assertEqual(
            "07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244",
            hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            "1e638aca270d3ff395e027feee2f30ddb6f58927b76bbe0a7875fcca9b199738",
            hashlib.sha256(ARTIFACT.read_bytes()).hexdigest(),
        )

    def test_inbound_commands_run_synchronously_on_the_main_queue(self) -> None:
        text = ARTIFACT.read_text()
        run = text.split("## __ZN9PSvDBMain3runEv |", 1)[1].split(
            "## __ZN9PSvDBMain10DisconnectEh |", 1
        )[0]
        self.assertEqual(
            2,
            run.count(
                "call      0x102521340  ; "
                "__ZN9PSvDBMain11OnClientReqEP16_struct_dbsm_msg"
            ),
        )
        self.assertIn("mov       r12d, 0x1f4", run)
        self.assertIn("__ZNK4juce13WaitableEvent4waitEd", run)

    def test_correlated_replies_use_the_shared_player_routed_queue(self) -> None:
        text = ARTIFACT.read_text()
        request = text.split(
            "## __ZN9PSvDBMain17RequestToSendDataEhP19_struct_db_comm_cmd |", 1
        )[1].split("## __ZN9PSvDBMain11OnClientReq", 1)[0]
        self.assertIn("mov       byte ptr [rax + 0xf], r12b", request)
        self.assertIn(
            "call      0x1013f5490  ; "
            "__ZN9PSvDBComm11PostMessageEP16_struct_dbsc_msg",
            request,
        )

    def test_disconnect_clears_player_state_and_requests_socket_drop(self) -> None:
        text = ARTIFACT.read_text()
        disconnect = text.split("## __ZN9PSvDBMain10DisconnectEh |", 1)[1].split(
            "## __ZN9PSvDBMain17PostServerMessage", 1
        )[0]
        self.assertIn("__ZN9PSvDBMain29ClearFilterConditionForPlayerEh", disconnect)
        self.assertIn("__ZN9PSvDBMain11clearAIOMapEh", disconnect)
        self.assertIn("__ZN9PSvDBComm13RequestToDropEh", disconnect)

    def test_empty_0100_is_a_connection_close_sentinel(self) -> None:
        text = CONNECTION.read_text()
        listen = text.split("## __ZN15PSvDBConnection6ListenEv |", 1)[1].split(
            "## __ZN15PSvDBConnection11IsConnectedEv |", 1
        )[0]
        self.assertIn("mov       dword ptr [rsp + 0x20], 0xfffffffe", listen)
        self.assertIn("mov       word ptr [rsp + 0x24], 0x100", listen)
        self.assertIn("__ZN15PSvDBConnection11SendCommandEP19_struct_db_comm_cmd", listen)

    def test_delivery_zero_count_is_queued_as_the_correlated_reply(self) -> None:
        builder = BUILDERS.read_text().split(
            "## __ZN9PSvDBMain14GetDeliveryInfEP16_struct_dbsm_msgjPm |", 1
        )[1].split("## __ZN9PSvDBMain14GetPlaySongInf", 1)[0]
        self.assertIn("mov       eax, dword ptr [rcx + 8]", builder)
        self.assertIn("mov       byte ptr [rbx + 0x13], 6", builder)

        handler = DISPATCH.read_text().split(
            "## __ZN9PSvDBMain12OnSongInfCmdEP16_struct_dbsm_msg |", 1
        )[1].split("## __ZN9PSvDBMain5isAIO", 1)[0]
        self.assertIn(
            "call      0x101ab8f10  ; "
            "__ZN9PSvDBMain14GetDeliveryInfEP16_struct_dbsm_msgjPm",
            handler,
        )
        self.assertIn(
            "call      0x102521600  ; "
            "__ZN9PSvDBMain16Ret4ByteToClientEP19_struct_db_comm_cmdih",
            handler,
        )


if __name__ == "__main__":
    unittest.main()
