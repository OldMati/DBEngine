from enum import Enum
from execution.expressions.base import Expression


class ComparisonOp(Enum):
    EQ = '='
    NEQ = '!='
    LT = '<'
    LTE = '<='
    GT = '>'
    GTE = '>='

class Comparison(Expression):
    def __init__(self, left: Expression, op: ComparisonOp, right: Expression):
        self.left = left
        self.op = op
        self.right = right
    
    def bind(self, schema):
        self.left.bind(schema)
        self.right.bind(schema)
    
    def evaluate(self, record = None, schema = None):
        l = self.left.evaluate(record, schema)
        r = self.right.evaluate(record, schema)

        match self.op:
            case ComparisonOp.EQ:  return l == r
            case ComparisonOp.NEQ: return l != r
            case ComparisonOp.LT:  return l < r
            case ComparisonOp.LTE: return l <= r
            case ComparisonOp.GT:  return l > r
            case ComparisonOp.GTE: return l >= r