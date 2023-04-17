from functools import partial
import sys
from typing import List, Sequence, Union, Optional


def _to_bytes(bss: List[Union[int, bytes]]) -> bytes:
    lb: List[bytes] = []
    for bs in bss:
        if isinstance(bs, bytes):
            lb.append(bs)
        elif isinstance(bs, int):
            lb.append(bs.to_bytes(1, byteorder='big'))
        else:
            raise ValueError(f"illegal list element: {bs}")
    return b''.join(lb)


class WasiEnvironment:
    """
    Simple WASI environment.

    FIXME(zhangwen): not thread-safe!  and assumes is only used by a single execution.
    FIXME(zhangwen): this really should be part of Manticore's WASM state.
    """
    ALL_FUNCTION_NAMES = (
        "args_get",
        "args_sizes_get",
        "environ_get",
        "environ_sizes_get",
        "clock_res_get",
        "clock_time_get",
        "fd_advise",
        "fd_close",
        "fd_datasync",
        "fd_fdstat_get",
        "fd_fdstat_set_flags",
        "fd_filestat_get",
        "fd_filestat_set_size",
        "fd_pread",
        "fd_prestat_get",
        "fd_prestat_dir_name",
        "fd_pwrite",
        "fd_read",
        "fd_readdir",
        "fd_renumber",
        "fd_seek",
        "fd_sync",
        "fd_tell",
        "fd_write",
        "path_create_directory",
        "path_filestat_get",
        "path_filestat_set_times",
        "path_link",
        "path_open",
        "path_readlink",
        "path_remove_directory",
        "path_rename",
        "path_symlink",
        "path_unlink_file",
        "poll_oneoff",
        "proc_exit",
        "random_get",
    )

    # For stdout and stderr.
    STD_FDSTAT = bytes((0x2, 0, 0, 0, 0, 0, 0, 0, 0xdb, 0x1, 0xe0, 0x8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,))
    STD_FILESTAT = bytes((0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))

    def __init__(self, args: Sequence[str], stdin: bytes = None) -> None:
        self.args = args
        self.exit_result = None
        self.stdin: bytes = stdin or b''
        self.stdout: List[bytes] = []

        env = {func_name: partial(self.func_missing, func_name) for func_name in self.ALL_FUNCTION_NAMES}  # Default.
        for attr_name in dir(self):
            if attr_name.startswith("_wasi_"):
                func_name = attr_name[len("_wasi_"):]
                env[func_name] = getattr(self, attr_name)
        self.env = env

    def get_env_dict(self):
        return self.env

    def get_exit_result(self) -> Optional[int]:
        return self.exit_result

    def get_stdout(self) -> bytes:
        return b''.join(self.stdout)

    @staticmethod
    def func_missing(func_name, _state, *args):
        arg_list = ", ".join(str(a) for a in args)
        print(f"Not implemented: {func_name}({arg_list})")
        raise NotImplementedError

    @staticmethod
    def _wasi_clock_time_get(state, _id, _precision, result_ptr):
        state.mem.write_int(result_ptr, 0, size=64)
        return [0]

    @staticmethod
    def _wasi_environ_sizes_get(state, num_var_ptr, data_size_ptr):
        state.mem.write_int(num_var_ptr, 0)
        state.mem.write_int(data_size_ptr, 0)
        return [0]

    def _wasi_args_sizes_get(self, state, argc_ptr, argv_size_ptr):
        state.mem.write_int(argc_ptr, len(self.args))
        state.mem.write_int(argv_size_ptr, sum(len(s)+1 for s in self.args))
        return [0]

    def _wasi_args_get(self, state, argv_ptr, argv_buf_ptr):
        for arg in self.args:
            state.mem.write_int(argv_ptr, argv_buf_ptr)
            argv_ptr += 4

            zero_terminated_bytes = arg.encode("ascii") + b'\0'
            state.mem.write_bytes(argv_buf_ptr, zero_terminated_bytes)
            argv_buf_ptr += len(zero_terminated_bytes)

        return [0]

    @staticmethod
    def _wasi_fd_prestat_get(_state, _fd, _out_ptr):
        # FIXME(zhangwen): what if 0 <= fd <= 2?
        return [8]  # badf

    def _wasi_proc_exit(self, _state, result):
        assert self.exit_result is None, f"process exited already with result: {self.exit_result}"
        self.exit_result = result
        return []

    @classmethod
    def _wasi_fd_fdstat_get(cls, state, fd, out_ptr):
        assert 0 <= fd <= 2, f"Unsupported fd: {fd}"
        state.mem.write_bytes(out_ptr, cls.STD_FDSTAT)
        return [0]

    @classmethod
    def _wasi_fd_filestat_get(cls, state, fd, out_ptr):
        assert 0 <= fd <= 2, f"Unsupported fd: {fd}"
        state.mem.write_bytes(out_ptr, cls.STD_FILESTAT)
        return [0]

    @staticmethod
    def _wasi_random_get(state, buf_ptr, buf_len):
        state.mem.write_bytes(buf_ptr, b'\0' * buf_len)
        return [0]

    def _wasi_fd_read(self, state, fd, iovs, iovs_len, out_ptr):
        assert fd == 0, f"Unsupported fd: {fd}"
        assert iovs_len == 1, f"Unsupported: iovs_len = {iovs_len} != 1"

        buf_ptr = state.mem.read_int(iovs)
        iovs += 4
        buf_len = state.mem.read_int(iovs)
        iovs += 4

        nb_read = min(len(self.stdin), buf_len)
        state.mem.write_bytes(buf_ptr, self.stdin[:nb_read])
        self.stdin = self.stdin[nb_read:]

        state.mem.write_int(out_ptr, nb_read)
        return [0]

    def _wasi_fd_write(self, state, fd, iovs, iovs_len, out_ptr):
        assert 1 <= fd <= 2, f"Unsupported fd: {fd}"
        nb_written = 0
        for i in range(iovs_len):
            buf_ptr = state.mem.read_int(iovs)
            iovs += 4
            buf_len = state.mem.read_int(iovs)
            iovs += 4

            buf_bytes = _to_bytes(state.mem.read_bytes(buf_ptr, buf_len))
            nb_written += sys.stdout.buffer.write(buf_bytes)
            self.stdout.append(buf_bytes)

        state.mem.write_int(out_ptr, nb_written)
        return [0]
