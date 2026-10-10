"""Bounded Decimal arithmetic for observed amounts and policy rates."""

from __future__ import annotations

import ast
from decimal import ROUND_FLOOR, ROUND_HALF_UP, Decimal, DecimalException, localcontext
from typing import Literal

from pydantic_ai import ModelRetry


def calculate(
    expression: str, rounding: Literal["none", "floor", "cents"] = "none"
) -> dict[str, str]:
    """Calculate a bounded Decimal numeric expression, without executing code.

    Only numbers, parentheses, unary signs and + - * / // are supported.
    Choose floor for whole-number points, or cents for half-up currency
    rounding. Derive inputs from observed rules and records, never guesses.
    """
    if len(expression) > 256:
        raise ModelRetry("Arithmetic expression is too long")
    try:
        tree = ast.parse(expression, mode="eval")
        if sum(1 for _ in ast.walk(tree)) > 64:
            raise ValueError("Arithmetic expression has too many operations")

        def evaluate(node: ast.AST) -> Decimal:
            if isinstance(node, ast.Constant) and type(node.value) in (int, float):
                value = Decimal(ast.get_source_segment(expression, node) or "")
            elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
                operand = evaluate(node.operand)
                value = operand if isinstance(node.op, ast.UAdd) else -operand
            elif isinstance(node, ast.BinOp):
                left, right = evaluate(node.left), evaluate(node.right)
                if isinstance(node.op, ast.Add):
                    value = left + right
                elif isinstance(node.op, ast.Sub):
                    value = left - right
                elif isinstance(node.op, ast.Mult):
                    value = left * right
                elif isinstance(node.op, ast.Div):
                    value = left / right
                elif isinstance(node.op, ast.FloorDiv):
                    value = (left / right).to_integral_value(rounding=ROUND_FLOOR)
                else:
                    raise ValueError("Unsupported arithmetic operator")
            else:
                raise ValueError("Only numeric literals and arithmetic operations are allowed")
            if not value.is_finite():
                raise ValueError("Arithmetic values must be finite")
            if abs(int(value.as_tuple().exponent)) > 64:
                raise ValueError("Arithmetic decimal exponents must remain within 64")
            if abs(value) > Decimal("1e12"):
                raise ValueError("Arithmetic values must remain finite and within 1e12")
            return value

        with localcontext() as context:
            context.prec = 40
            value = evaluate(tree.body)
            if rounding == "floor":
                value = value.to_integral_value(rounding=ROUND_FLOOR)
            elif rounding == "cents":
                value = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            elif rounding != "none":
                raise ValueError("Unknown rounding mode")
    except (SyntaxError, ValueError, DecimalException) as error:
        raise ModelRetry(f"Invalid bounded arithmetic: {error}") from error
    return {"expression": expression, "value": format(value, "f"), "rounding": rounding}
