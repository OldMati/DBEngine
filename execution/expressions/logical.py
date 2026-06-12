from  execution.expressions.base import Expression

class And(Expression):
    def __init__(self, left: Expression, right: Expression):
        self.left = left
        self.right = right
    
    def bind(self, schema):
        self.left.bind(schema)
        self.right.bind(schema)

    def evaluate(self, record, schema):
        l = self.left.evaluate(record, schema)
        r = self.right.evaluate(record, schema)
        return l and r
    

class Or(Expression):
    def __init__(self, left: Expression, right: Expression):
        self.left = left
        self.right = right
    
    def bind(self, schema):
        self.left.bind(schema)
        self.right.bind(schema)

    def evaluate(self, record, schema):
        l = self.left.evaluate(record, schema)
        r = self.right.evaluate(record, schema)
        return l or r