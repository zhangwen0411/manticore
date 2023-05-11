from manticore.core.plugin import Plugin
from manticore.utils import config
from manticore.utils.enums import MProcessingType
from manticore.wasm import ManticoreWASM
from manticore.wasm.structure import WASIEnvironmentConfig

FILENAME = "arglen.wasm"
ARGS = (FILENAME, "hello world!!")


class TestPlugin(Plugin):
    def will_terminate_state_callback(self, state, *_args) -> None:
        wasi_env = state.platform.wasi_env
        actual_stdout = wasi_env.get_stdout()
        expected_stdout = (str(len(ARGS[1])) + "\n").encode("ascii")
        if actual_stdout == expected_stdout:
            print(f"PASS: Stdout check ({actual_stdout})")
        else:
            print(f"FAIL: actual stdout ({actual_stdout}) != expected out ({expected_stdout})")

        exit_result = wasi_env.get_exit_result()
        if exit_result is None or exit_result == 0:
            print(f"PASS: Exit result check ({exit_result})")
        else:
            print(f"FAIL: abnormal exit: {exit_result}")


def main():
    core_group = config.get_group("core")
    core_group.mprocessing = MProcessingType.single
    core_group.compress_states = False

    m = ManticoreWASM(FILENAME, stub_missing=False, workspace_url="non_serializing:",
                      wasi_config=WASIEnvironmentConfig(args=ARGS))
    m.register_plugin(TestPlugin())
    m._start()


if __name__ == '__main__':
    main()
