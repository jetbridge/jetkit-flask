from typing import TYPE_CHECKING
from abc import abstractmethod

if TYPE_CHECKING:
    import jetkit.model.user


class Owned:
    """Protocol for models that have an `owner` user."""

    @property
    @abstractmethod
    def id(self):
        ...

    @property
    @abstractmethod
    def owner(self) -> "jetkit.model.user.CoreUser":
        ...
