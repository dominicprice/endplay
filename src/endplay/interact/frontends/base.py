import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from endplay.interact.commandobject import CommandObject


class BaseFrontend(abc.ABC):
    @abc.abstractmethod
    def __init__(self, cmdobj: "CommandObject"):
        ...

    @abc.abstractmethod
    def interact(self) -> None:
        ...
