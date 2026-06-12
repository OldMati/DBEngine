from execution.operators.base import Operator
from execution.expressions.base import Expression

class Filter(Operator):
    child: Operator
    predicate: Expression

    def open(self, child: Operator, predicate: Expression):
        self.child = child
        self.predicate = predicate
        self.schema = self.child.output_schema()
        predicate.bind(self.schema)
        child.open()
    
    def next(self):
        for values in self.child.next():
            if self.predicate.evaluate(values, self.schema):
                yield values

    def output_schema(self):
        return self.schema
    
    def close(self):
        self.child.close()