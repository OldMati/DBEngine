from execution.planner.logical import *
from execution.expressions.column_ref import ColumnRef
from execution.expressions.logical import And

class QueryOptimizer:

    def optimize(self, node: LogicalNode) -> LogicalNode:
        return self.push_down(node)

    def push_down(self, node: LogicalNode) -> LogicalNode:

        for attr in ('left', 'right', 'child'):
            sub = getattr(node, attr, None)
            if sub is not None:
                setattr(node, attr, self.push_down(sub))

        if isinstance(node, LogicalFilter):
            return self.push_filter(node)
        return node
        
    def push_filter(self, filter_node: LogicalFilter) -> LogicalNode:
        residual = []
        for conjuct in self.split_conjuncts(filter_node.predicate):
            tables = self.referenced_tables(conjuct)
            if len(tables) == 1:
                scan = self.find_scan(filter_node.child, next(iter(tables)))
                if scan is not None:
                    self.push_into_scan(scan, conjuct)
                    continue
            residual.append(conjuct)
        
        combined = self.combine_conjuncts(residual)
        if combined is None:
            return filter_node.child
        
        filter_node.predicate = combined
        return filter_node


    def split_conjuncts(self, predicate) -> list:
        if isinstance(predicate, And):
            return self.split_conjuncts(predicate.left) + self.split_conjuncts(predicate.right)
        return [predicate]

    def combine_conjuncts(self, conjuncts: list):
        if not conjuncts:
            return None
        
        combined = conjuncts[0]
        for c in conjuncts[1:]:
            combined = And(combined, c)
        
        return combined

    def referenced_tables(self, expr) -> set:
        tables = set()
        self.collect_tables(expr, tables)
        return tables
    
    def collect_tables(self, expr, tables: set):
        if isinstance(expr, ColumnRef):
            name = expr.column_name
            tables.add(name.split('.')[0] if '.' in name else name)
            return
        
        for attr in ('left', 'right'):
            sub = getattr(expr, attr, None)
            if sub is not None:
                self.collect_tables(sub, tables)
    
    def find_scan(self, node, table: str):
        if isinstance(node, LogicalScan):
            if node.table_name == table:
                return node
            return None
        
        for attr in ('left', 'right', 'child'):
            sub = getattr(node, attr, None)
            if sub is not None:
                found = self.find_scan(sub, table)
                if found is not None:
                    return found
        return None

    def push_into_scan(self, scan:LogicalScan, predicate):
        if scan.predicate is None:
            scan.predicate = predicate
        else:
            scan.predicate = And(scan.predicate, predicate)

