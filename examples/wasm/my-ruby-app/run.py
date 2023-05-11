import sys

from manticore.core.plugin import Plugin
from manticore.utils import config
from manticore.utils.enums import MProcessingType
from manticore.wasm import ManticoreWASM
from manticore.wasm.structure import WASIEnvironmentConfig


class PrintResultPlugin(Plugin):
    def will_terminate_state_callback(self, state, *_args) -> None:
        wasi_env = state.platform.wasi_env
        sys.stdout.buffer.write(wasi_env.get_stdout())

        print("=====")
        print(f"Exit result: {wasi_env.get_exit_result()}")


def main():
    # manticore.set_verbosity(5)
    core_group = config.get_group("core")
    core_group.mprocessing = MProcessingType.single
    core_group.compress_states = False

    m = ManticoreWASM("my-ruby-app.wasm", stub_missing=False, workspace_url="non_serializing:",
                      wasi_config=WASIEnvironmentConfig(args=("my-ruby-app.wasm", "-v")))
    m.register_plugin(PrintResultPlugin())
    m._start()


if __name__ == "__main__":
    main()
