from abc import ABC, abstractmethod
from catalog.schema import Schema

class Expression(ABC):
    @abstractmethod
    def evaluate(self, record, schema):
        pass