from catalog.schema import Column, DataType, Schema
from execution.expressions.base import Expression
from execution.expressions.column_ref import ColumnRef
from execution.operators.base import Operator


class Projection(Operator):
    """Evaluates a select list, narrowing each row to the chosen columns."""

    child: Operator
    expressions: list[Expression]

    def open(self, child: Operator, projections: list[tuple[Expression, str]]):
        self.child = child
        self.input_schema = child.output_schema()

        self.expressions = [expr for expr, _ in projections]
        for expr in self.expressions:
            expr.bind(self.input_schema)

        names = [name for _, name in projections]
        self.schema = self._build_output_schema(names)

    def _build_output_schema(self, names: list[str]) -> Schema:
        """Carry column types through from the input schema where possible."""
        columns = []
        for expr, name in zip(self.expressions, names):
            source = self._source_column(expr)
            if source is not None:
                columns.append(Column(name, source.type, source.max_length))
            else:
                columns.append(Column(name, DataType.VARCHAR))
        return Schema(columns)

    def _source_column(self, expr: Expression) -> Column | None:
        """The input column an expression reads, if it is a plain reference."""
        if not isinstance(expr, ColumnRef):
            return None
        name = expr.column_name.split('.')[-1]
        if name not in self.input_schema.column_names:
            return None
        return self.input_schema.columns[self.input_schema.column_names[name]]

    def next(self):
        for values in self.child.next():
            yield tuple(
                expr.evaluate(values, self.input_schema) for expr in self.expressions
            )

    def output_schema(self):
        return self.schema

    def close(self):
        self.child.close()