import unittest

from manticore.core.plugin import Plugin
from manticore.utils import config
from manticore.utils.enums import MProcessingType
from manticore.wasm import ManticoreWASM
from manticore.wasm.structure import WASIEnvironmentConfig


class CaptureResultPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.results = set()

    def will_terminate_state_callback(self, state, *_args) -> None:
        wasi_env = state.platform.wasi_env
        self.results.add(wasi_env.get_exit_result())


class TestReadHex(unittest.TestCase):
    FILENAME = "read_hex.wasm"
    ARGS = (FILENAME,)

    def setUp(self) -> None:
        core_group = config.get_group("core")
        core_group.mprocessing = MProcessingType.single
        core_group.compress_states = False

    def _assert_exit_value(self, *, stdin: str, expected_exit_value: int) -> None:
        plugin = CaptureResultPlugin()
        m = ManticoreWASM(self.FILENAME, stub_missing=False,
                          workspace_url="non_serializing:",
                          wasi_config=WASIEnvironmentConfig(args=self.ARGS, stdin=stdin.encode("ascii")))
        m.register_plugin(plugin)
        m._start()

        exit_values = plugin.results
        self.assertEqual(len(exit_values), 1)
        exit_value = next(iter(exit_values))
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

    @staticmethod
    def _stdin_gen(_state):
        x = _state.new_symbolic_value(8, "stdin_0")
        y = _state.new_symbolic_value(8, "stdin_1")
        _state.constrain(x >= 0x30)
        _state.constrain(x <= 0x39)
        _state.constrain(y >= ord('a'))
        _state.constrain(y <= ord('f'))
        return [x, y]

    def test_symbolic_two_bytes(self):
        m = ManticoreWASM(self.FILENAME, stub_missing=False, workspace_url="mem:",
                          wasi_config=WASIEnvironmentConfig(args=self.ARGS, stdin=self._stdin_gen))
        plugin = CaptureResultPlugin()
        m.register_plugin(plugin)
        m._start()

        self.assertEqual(plugin.results, {0, 1, 2, 3})

        # m.finalize()


if __name__ == '__main__':
    unittest.main()
