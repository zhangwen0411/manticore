from typing import Dict

from .abstract_workspace import AbstractWorkspace
from .state import StateBase


class NonSerializingWorkspace(AbstractWorkspace):
    """A workspace that doesn't serialize state.  Should only be used under single-threaded execution."""
    def __init__(self):
        self._next_id = 0
        self._store: Dict[int, StateBase] = {}  # Maps state ID to state.

    @property
    def uri(self) -> str:
        return "non_serializing"

    def load_state(self, state_id: int, delete=True) -> StateBase:
        state = self._store[state_id]
        if delete:
            del self._store[state_id]
        return state

    def save_state(self, state: StateBase, state_id: int = None) -> int:
        if state_id is None:
            state_id = self._next_id
            self._next_id += 1

        self._store[state_id] = state
        return state_id

    def rm_state(self, state_id: int) -> None:
        del self._store[state_id]
