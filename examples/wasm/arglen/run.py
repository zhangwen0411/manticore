from functools import partial
import sys
from typing import List, Union

from manticore.utils import config
from manticore.utils.enums import MProcessingType
from manticore.wasm import ManticoreWASM

FILENAME = "arglen.wasm"
ARGS = [FILENAME, "hello world!!"]

FDSTAT = bytes((0x2, 0, 0, 0, 0, 0, 0, 0, 0xdb, 0x1, 0xe0, 0x8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,))

STDOUT: List[bytes] = []
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


def fd_fdstat_get(state, fd, out_ptr):
    assert 0 <= fd <= 2, f"Unsupported fd: {fd}"
    state.mem.write_bytes(out_ptr, FDSTAT)
    return [0]


def _to_bytes(bss: List[Union[int, bytes]]) -> bytes:
    lb = []
    for bs in bss:
        if isinstance(bs, bytes):
            lb.append(bs)
        elif isinstance(bs, int):
            lb.append(bs.to_bytes(1, byteorder='big'))
        else:
            raise ValueError(f"illegal list element: {bs}")
    return b''.join(lb)


def fd_write(state, fd, iovs, iovs_len, out_ptr):
    assert 1 <= fd <= 2, f"Unsupported fd: {fd}"
    nb_written = 0
    for i in range(iovs_len):
        buf_ptr = state.mem.read_int(iovs)
        iovs += 4
        buf_len = state.mem.read_int(iovs)
        iovs += 4

        buf_bytes = _to_bytes(state.mem.read_bytes(buf_ptr, buf_len))
        STDOUT.append(buf_bytes)
        sys.stdout.buffer.write(buf_bytes)
        nb_written += len(buf_bytes)

    state.mem.write_int(out_ptr, nb_written)
    return [0]


def mock(name, _state, *args):
    print(f"{name}({args})")
    raise NotImplementedError


def main():
    core_group = config.get_group("core")
    core_group.mprocessing = MProcessingType.single
    core_group.compress_states = False

    env = dict(args_sizes_get=args_sizes_get, args_get=args_get, proc_exit=proc_exit,
               fd_close=partial(mock, "fd_close"),
               fd_fdstat_get=fd_fdstat_get,
               fd_seek=partial(mock, "fd_seek"), fd_write=fd_write)
    m = ManticoreWASM(FILENAME, sup_env={"wasi_snapshot_preview1": env}, stub_missing=False,
                      workspace_url="non_serializing:")
    m._start()

    assert b''.join(STDOUT).decode("ascii") == str(len(ARGS[1])) + "\n"
    assert EXIT_VALUE is None or EXIT_VALUE == 0, f"abnormal exit: {EXIT_VALUE}"


if __name__ == '__main__':
    main()
