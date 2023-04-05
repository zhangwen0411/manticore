import tempfile

from manticore.wasm import ManticoreWASM

FILENAME = "arglen.wasm"
ARGS = [FILENAME, "hello world!!"]

EXIT_VALUE = None


def args_sizes_get(state, argc_ptr, argv_size_ptr):
    state.mem.write_int(argc_ptr, len(ARGS))
    state.mem.write_int(argv_size_ptr, sum(len(s)+1 for s in ARGS))
    return [0]

def args_get(state, argv_ptr, argv_buf_ptr):
    for arg in ARGS:
        state.mem.write_int(argv_ptr, argv_buf_ptr)
        argv_ptr += 4

        zero_terminated_bytes = arg.encode("ascii") + b'\0'
        state.mem.write_bytes(argv_buf_ptr, zero_terminated_bytes)
        argv_buf_ptr += len(zero_terminated_bytes)

    return [0]


def proc_exit(_state, result):
    global EXIT_VALUE
    assert EXIT_VALUE is None
    EXIT_VALUE = result
    return []


def main():
    env = dict(args_sizes_get=args_sizes_get, args_get=args_get, proc_exit=proc_exit)
    with tempfile.TemporaryDirectory() as d:
        m = ManticoreWASM(FILENAME, sup_env={"wasi_snapshot_preview1": env}, stub_missing=False, workspace_url=d)
        m._start()

    assert EXIT_VALUE == len(ARGS[1])


if __name__ == '__main__':
    main()
