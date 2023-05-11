from manticore.core.plugin import Plugin
from manticore.wasm import ManticoreWASM
from manticore.wasm.state import State
from manticore.utils import config
from manticore.utils.enums import MProcessingType


def arg_gen(state):
    arg = state.new_symbolic_value(32, "identity_arg")
    state.constrain(arg >= 30)
    state.constrain(arg <= 50)
    return [arg]


class PrintRetPlugin(Plugin):
    """A plugin that looks for states that returned zero and solves for their inputs"""
    def will_terminate_state_callback(self, state: State, *args):
        retval = state.stack.peek()
        state.constrain(retval == 42)
        if state.is_feasible():
            print("Solution found!")
            input_symbols = state.input_symbols
            values = state.solve_one_n_batched(input_symbols)
            for sym, solved in zip(input_symbols, values):
                print(f"{sym.name}: {solved}")


if __name__ == "__main__":
    core_group = config.get_group("core")
    core_group.mprocessing = MProcessingType.single
    core_group.compress_states = False

    m = ManticoreWASM("identity.wasm", workspace_url="non_serializing:")

    # Register our state termination callback
    m.register_plugin(PrintRetPlugin())

    # Run the main function, which will call getchar
    m.id(arg_gen)

    # Save a copy of the inputs to the disk
    m.finalize()
