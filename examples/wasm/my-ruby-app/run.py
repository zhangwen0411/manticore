"""
The Ruby source at `/src/my_app.rb` prints out "hello".
"""
import os
import sys
from timeit import default_timer as timer

from manticore.core.plugin import Plugin
from manticore.utils import config
from manticore.utils.enums import MProcessingType
from manticore.wasm import ManticoreWASM
from manticore.wasm.structure import WASIEnvironmentConfig


class PrintResultPlugin(Plugin):
    FIFO_PATH = "/tmp/my-ruby-instr"

    def __init__(self):
        super().__init__()
        self.prev_print_ts = 0
        self.prev_print_inst_count = 0
        self.prev_inst_ts = timer()
        self.inst_count = 0

        os.mkfifo(self.FIFO_PATH)
        self.fifo = open(self.FIFO_PATH, 'w')

    def will_execute_instruction_callback(self, _state, inst) -> None:
        now = timer()
        dur_prev_inst, self.prev_inst_ts = now - self.prev_inst_ts, now
        print(self.inst_count, int(dur_prev_inst*1000*1000), inst, file=self.fifo)
        self.inst_count += 1

        dur = now - self.prev_print_ts
        if dur >= 10:
            self.prev_print_ts = now

            inst_count_diff = self.inst_count - self.prev_print_inst_count
            self.prev_print_inst_count = self.inst_count

            print(f"{dur}\t{inst_count_diff}\t{now}\t{self.inst_count}")

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
                      wasi_config=WASIEnvironmentConfig(args=("my-ruby-app.wasm",
                                                              # "-v"
                                                              "/src/my_app.rb"
                                                              )))
    plugin = PrintResultPlugin()
    m.register_plugin(plugin)
    m._start()

    print(f"Final instruction count:\t{plugin.inst_count}")


if __name__ == "__main__":
    main()
