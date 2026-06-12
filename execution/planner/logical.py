from dataclasses import dataclass
from typing import Optional
from execution.expressions.base import Expression

@dataclass
class LogicalNode:
    pass

@dataclass
class LogicalScan(LogicalNode):
    table_name: str
    alias: Optional[str] = None

    def __repr__(self):
        return f"LogicalScan({self.table_name})"

@dataclass
class LogicalFilter(LogicalNode):
    child: LogicalNode
    predicate: Expression
    
    def __repr__(self):
        return f"LogicalFilter({self.predicate})\n  └── {self.child}"

@dataclass
class LogicalProjection(LogicalNode):
    child: LogicalNode
    columns: list[str]

    def __repr__(self):
        return f"LogicalProjection({self.columns})\n  └── {self.child}"

@dataclass
class LogicalJoin(LogicalNode):
    left: LogicalNode
    right: LogicalNode
    condition: Expression    
    
    def __repr__(self):
        return f"LogicalJoin({self.condition})\n  ├── {self.left}\n  └── {self.right}"
