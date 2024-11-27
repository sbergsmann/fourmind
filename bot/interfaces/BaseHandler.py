""""""

from abc import ABC, abstractmethod
from typing import Any


class BaseHandler(ABC):
    __storage: Any

    @abstractmethod
    def get(self, id: int) -> Any | None:
        raise NotImplementedError

    @abstractmethod
    def add(self, obj: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    def remove(self, id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def remove_async(self, id: int) -> None:
        raise NotImplementedError
