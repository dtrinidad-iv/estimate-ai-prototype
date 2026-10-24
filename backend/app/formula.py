"""A tiny, safe expression evaluator for price-book formulas.

Formulas like "eaves_ft * 2 + valleys_ft" or "squares if 8 <= pitch < 10 else 0" are
stored as data so estimators can change them without code changes. Only arithmetic,
comparisons and conditionals are allowed; everything is computed with Decimal.
"""

import ast
import operator
from decimal import Decimal

_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
_CMP = {ast.Lt: operator.lt, ast.LtE: operator.le, ast.Gt: operator.gt, ast.GtE: operator.ge,
        ast.Eq: operator.eq, ast.NotEq: operator.ne}
_FUNCS = {"min": min, "max": max}


class FormulaError(ValueError):
    pass


def evaluate(expr: str, variables: dict[str, Decimal]) -> Decimal:
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise FormulaError(f"Invalid formula {expr!r}: {e.msg}") from e
    return _eval(tree.body, variables)


def _eval(node, v):
    match node:
        case ast.Constant(value=int() | float() as n) if not isinstance(n, bool):
            return Decimal(str(n))
        case ast.Name(id=name):
            if name not in v:
                raise FormulaError(f"Unknown variable {name!r}")
            return v[name]
        case ast.BinOp(left=l, op=op, right=r) if type(op) in _BIN:
            right = _eval(r, v)
            if isinstance(op, ast.Div) and right == 0:
                return Decimal(0)
            return _BIN[type(op)](_eval(l, v), right)
        case ast.UnaryOp(op=ast.USub(), operand=o):
            return -_eval(o, v)
        case ast.Compare(left=l, ops=ops, comparators=comps):
            left = _eval(l, v)
            for op, comp in zip(ops, comps):
                if type(op) not in _CMP:
                    raise FormulaError("Unsupported comparison")
                right = _eval(comp, v)
                if not _CMP[type(op)](left, right):
                    return Decimal(0)
                left = right
            return Decimal(1)
        case ast.IfExp(test=t, body=b, orelse=e):
            return _eval(b, v) if _eval(t, v) else _eval(e, v)
        case ast.BoolOp(op=ast.And(), values=vals):
            return Decimal(1) if all(_eval(x, v) for x in vals) else Decimal(0)
        case ast.BoolOp(op=ast.Or(), values=vals):
            return Decimal(1) if any(_eval(x, v) for x in vals) else Decimal(0)
        case ast.Call(func=ast.Name(id=fn), args=args) if fn in _FUNCS:
            return _FUNCS[fn](*(_eval(a, v) for a in args))
    raise FormulaError(f"Unsupported expression: {ast.unparse(node)}")
