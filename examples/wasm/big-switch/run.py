from manticore.core.plugin import Plugin
from manticore.wasm import ManticoreWASM
from manticore.utils import config
from manticore.utils.enums import MProcessingType
from manticore.wasm.structure import WASIEnvironmentConfig


class CaptureResultPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.results = set()

    def will_terminate_state_callback(self, state, *_args) -> None:
        wasi_env = state.platform.wasi_env
        self.results.add(wasi_env.get_exit_result())


def main():
    # manticore.set_verbosity(5)
    core_group = config.get_group("core")
    core_group.mprocessing = MProcessingType.single
    core_group.compress_states = False

    m = ManticoreWASM("big-switch.wasm", stub_missing=False, workspace_url="non_serializing:",
                      wasi_config=WASIEnvironmentConfig(args=("big-switch.wasm",
                                                              "a", "b")))
    plugin = CaptureResultPlugin()
    m.register_plugin(plugin)
    m._start()

    results = plugin.results
    assert len(results) == 1
    assert next(iter(results)) == 95


if __name__ == "__main__":
    main()
