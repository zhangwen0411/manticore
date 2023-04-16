import manticore
from manticore.utils import config
from manticore.utils.wasi_environment import WasiEnvironment
from manticore.utils.enums import MProcessingType
from manticore.wasm import ManticoreWASM


def main():
    # manticore.set_verbosity(5)
    core_group = config.get_group("core")
    core_group.mprocessing = MProcessingType.single
    core_group.compress_states = False

    wasi_env = WasiEnvironment(["my-ruby-app.wasm", "-v"])
    # wasi_env = WasiEnvironment(["my-ruby-app.wasm", "/src/my_app.rb"])
    env_dict = wasi_env.get_env_dict()
    # with TemporaryDirectory() as d:
    m = ManticoreWASM("my-ruby-app.wasm", sup_env={"wasi_snapshot_preview1": env_dict}, stub_missing=False, workspace_url="non_serializing:")
    m._start()
    print(f"Exit result: {wasi_env.get_exit_result()}")


if __name__ == "__main__":
    main()
