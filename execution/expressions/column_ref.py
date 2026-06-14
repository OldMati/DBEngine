from execution.expressions.base import Expression
from catalog.schema import Schema

class ColumnRef(Expression):

    def __init__(self, column_name: str):
        self._index = None
        self.column_name = column_name
    
    def bind(self, schema):
        self._index = schema.get_index(self.column_name)
    
    def evaluate(self, record: tuple, schema: Schema):
        return record[self._index]