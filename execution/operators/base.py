from abc import ABC, abstractmethod
from catalog.schema import Schema, Column

class Operator(ABC):

    @abstractmethod
    def open(self):
        pass

    @abstractmethod
    def next(self):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def output_schema(self) -> Schema:
        pass