from abc import ABC, abstractmethod

from manticore.core.state import StateBase


class AbstractWorkspace(ABC):
    @property
    @abstractmethod
    def uri(self) -> str:
        ...

    @abstractmethod
    def load_state(self, state_id: int, delete=True) -> StateBase:
        ...

    @abstractmethod
    def save_state(self, state: StateBase, state_id: int = None) -> int:
        ...

    @abstractmethod
    def rm_state(self, state_id: int) -> None:
        ...
