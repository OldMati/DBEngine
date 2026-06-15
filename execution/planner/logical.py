from dataclasses import dataclass
from typing import Optional
from execution.expressions.base import Expression
from catalog.schema import Column

@dataclass
class LogicalNode:
    pass

@dataclass
class LogicalScan(LogicalNode):
    table_name: str
    alias: Optional[str] = None
    predicate: Optional[Expression] = None
    yield_rid: bool = False

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

@dataclass
class LogicalCreateTable(LogicalNode):
    table_name: str
    columns: list[Column]

@dataclass
class LogicalInsert(LogicalNode):
    table_name: str
    values: list[tuple]

@dataclass
class LogicalTableDrop(LogicalNode):
    table_name: str

@dataclass
class LogicalDelete(LogicalNode):
    child: LogicalNode
    table_name: str

@dataclass
class LogicalDescribe(LogicalNode):
    table_name: str

@dataclass
class LogicalCreateIndex(LogicalNode):
    index_name: str
    table_name: str
    column_names: list[str]