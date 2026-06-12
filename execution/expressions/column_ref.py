from execution.expressions.base import Expression
from catalog.schema import Schema

class ColumnRef(Expression):

    def __init__(self, column_name: str):
        self.column_name: column_name
        self._index = None
    
    def bind(self, schema: Schema):
        self._index = schema.get_index(self.column_name)
    
    def evaluate(self, record: tuple, schema: Schema):
        return record[self._index]