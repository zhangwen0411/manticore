import tempfile

import manticore
from manticore.wasm import ManticoreWASM

def main():
    manticore.set_verbosity(5)

    env = {}
    with tempfile.TemporaryDirectory() as d:
        m = ManticoreWASM("arglen.wasm", sup_env={"wasi_snapshot_preview1": env}, workspace_url=d)
        m.invoke("_start")


if __name__ == '__main__':
    main()
