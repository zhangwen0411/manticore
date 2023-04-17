import unittest

from manticore.utils import config
from manticore.utils.enums import MProcessingType
from manticore.utils.wasi_environment import WasiEnvironment
from manticore.wasm import ManticoreWASM


class TestReadHex(unittest.TestCase):
    FILENAME = "read_hex.wasm"
    ARGS = [FILENAME]

    def setUp(self) -> None:
        core_group = config.get_group("core")
        core_group.mprocessing = MProcessingType.single
        core_group.compress_states = False

    def _assert_exit_value(self, *, stdin: str, expected_exit_value: int) -> None:
        wasi_env = WasiEnvironment(self.ARGS, stdin=stdin.encode("ascii"))
        env_dict = wasi_env.get_env_dict()
        m = ManticoreWASM(self.FILENAME, sup_env={"wasi_snapshot_preview1": env_dict}, stub_missing=False,
                          workspace_url="non_serializing:")
        m._start()

        exit_value = wasi_env.get_exit_result()
        if exit_value is None:
            self.assertEqual(expected_exit_value, 0)
        else:
            self.assertEqual(exit_value, expected_exit_value)

    def test_empty_stdin(self):
        self._assert_exit_value(stdin="", expected_exit_value=-1)

    def test_number(self):
        self._assert_exit_value(stdin="2", expected_exit_value=2)

    def test_another_number(self):
        self._assert_exit_value(stdin="deadbeef", expected_exit_value=0xdeadbeef & 3)


if __name__ == '__main__':
    unittest.main()
