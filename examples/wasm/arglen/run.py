from manticore.utils import config
from manticore.utils.enums import MProcessingType
from manticore.utils.wasi_environment import WasiEnvironment
from manticore.wasm import ManticoreWASM

FILENAME = "arglen.wasm"
ARGS = [FILENAME, "hello world!!"]


def main():
    core_group = config.get_group("core")
    core_group.mprocessing = MProcessingType.single
    core_group.compress_states = False

    wasi_env = WasiEnvironment(ARGS)
    env_dict = wasi_env.get_env_dict()
    m = ManticoreWASM(FILENAME, sup_env={"wasi_snapshot_preview1": env_dict}, stub_missing=False,
                      workspace_url="non_serializing:")
    m._start()

    assert wasi_env.get_stdout().decode("ascii") == str(len(ARGS[1])) + "\n"
    exit_result = wasi_env.get_exit_result()
    assert exit_result is None or exit_result == 0, f"abnormal exit: {exit_result}"


if __name__ == '__main__':
    main()
