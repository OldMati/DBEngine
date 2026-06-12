from execution.expressions.base import Expression

class Literal(Expression):
    '''A constant value'''

    def __init__(self, value):
        self.value = value

    def evaluate(self, record = None, schema = None):
        return self.value
        