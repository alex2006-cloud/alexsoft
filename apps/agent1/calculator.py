"""Safe arithmetic evaluator for the Agent1 calculator tool (stdlib only)."""
from __future__ import annotations

import ast
import math
import operator
from typing import Any, Callable

MAX_EXPRESSION_LENGTH = 500
MAX_POW_EXPONENT = 1000
MAX_RESULT_DIGITS = 10000
MAX_FACTORIAL_ARG = 1000


class CalculatorError(ValueError):
    """Carries a user-facing explanation of why an expression cannot be computed."""


_BIN_OPS: dict[type[ast.operator], Callable[[Any, Any], Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPS: dict[type[ast.unaryop], Callable[[Any], Any]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_MATH_FUNCTIONS = (
    "sqrt",
    "exp",
    "log",
    "log2",
    "log10",
    "sin",
    "cos",
    "tan",
    "asin",
    "acos",
    "atan",
    "atan2",
    "sinh",
    "cosh",
    "tanh",
    "degrees",
    "radians",
    "factorial",
    "ceil",
    "floor",
    "hypot",
    "fabs",
)

_FUNCTIONS: dict[str, Callable[..., Any]] = {
    name: getattr(math, name) for name in _MATH_FUNCTIONS
}
_FUNCTIONS.update({"abs": abs, "round": round, "min": min, "max": max})

_CONSTANTS: dict[str, float] = {"pi": math.pi, "e": math.e, "tau": math.tau}

_OP_NAMES: dict[type[ast.AST], str] = {
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "*",
    ast.Div: "/",
    ast.FloorDiv: "//",
    ast.Mod: "%",
    ast.Pow: "**",
}


def normalize(expression: str) -> str:
    """Trim, drop a leading '=' and accept '^' as the power operator."""
    expr = (expression or "").strip()
    if expr.startswith("="):
        expr = expr[1:].strip()
    if not expr:
        raise CalculatorError("пустое выражение")
    if len(expr) > MAX_EXPRESSION_LENGTH:
        raise CalculatorError(
            f"выражение длиннее {MAX_EXPRESSION_LENGTH} символов — разбейте его на части"
        )
    return expr.replace("^", "**")


def evaluate(expression: str) -> int | float:
    """Evaluate a whitelisted arithmetic expression; raise CalculatorError on anything else."""
    expr = normalize(expression)
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise CalculatorError(f"не удалось разобрать выражение «{expr}»: {exc.msg}") from exc
    return _eval(tree.body)


def format_number(value: int | float) -> str:
    if isinstance(value, int):
        return str(value)
    if value.is_integer() and abs(value) < 1e15:
        return str(int(value))
    return repr(value)


def calculate(expression: str) -> str:
    """Return '<normalized expression> = <result>' or raise CalculatorError."""
    expr = normalize(expression)
    return f"{expr} = {format_number(evaluate(expr))}"


def _eval(node: ast.AST) -> int | float:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise CalculatorError(f"допустимы только числа, получено: {node.value!r}")
        return node.value

    if isinstance(node, ast.UnaryOp):
        op = _UNARY_OPS.get(type(node.op))
        if op is None:
            raise CalculatorError("допустимы только унарные + и -")
        return _apply(op, _eval(node.operand))

    if isinstance(node, ast.BinOp):
        op = _BIN_OPS.get(type(node.op))
        if op is None:
            raise CalculatorError("допустимы только операторы + - * / // % **")
        left = _eval(node.left)
        right = _eval(node.right)
        if isinstance(node.op, ast.Pow):
            _check_pow(left, right)
        return _apply(op, left, right, name=_OP_NAMES.get(type(node.op)))

    if isinstance(node, ast.Name):
        if node.id in _CONSTANTS:
            return _CONSTANTS[node.id]
        raise CalculatorError(
            f"неизвестное имя «{node.id}»; доступны константы: {', '.join(sorted(_CONSTANTS))}"
        )

    if isinstance(node, ast.Call):
        return _eval_call(node)

    raise CalculatorError(
        "выражение содержит недопустимую конструкцию — нужны только числа, "
        "арифметические операторы и разрешённые функции"
    )


def _eval_call(node: ast.Call) -> int | float:
    if not isinstance(node.func, ast.Name):
        raise CalculatorError("вызывать можно только разрешённые функции по имени")
    name = node.func.id
    func = _FUNCTIONS.get(name)
    if func is None:
        raise CalculatorError(
            f"неизвестная функция «{name}»; доступны: {', '.join(sorted(_FUNCTIONS))}"
        )
    if node.keywords:
        raise CalculatorError(f"функция {name} вызывается только позиционными аргументами")
    args = [_eval(arg) for arg in node.args]
    if name == "factorial":
        _check_factorial(args)
    return _apply(func, *args, name=name)


def _check_pow(base: int | float, exponent: int | float) -> None:
    if abs(exponent) > MAX_POW_EXPONENT:
        raise CalculatorError(
            f"показатель степени больше {MAX_POW_EXPONENT} — такой расчёт не выполняется"
        )
    if base not in (0, 1, -1) and abs(exponent) * math.log10(abs(base)) > MAX_RESULT_DIGITS:
        raise CalculatorError(
            f"результат длиннее {MAX_RESULT_DIGITS} знаков — такой расчёт не выполняется"
        )


def _check_factorial(args: list[int | float]) -> None:
    if len(args) != 1:
        raise CalculatorError("factorial принимает один аргумент")
    value = args[0]
    if isinstance(value, float) and not value.is_integer():
        raise CalculatorError("factorial определён только для целых неотрицательных чисел")
    if value < 0:
        raise CalculatorError("factorial определён только для неотрицательных чисел")
    if value > MAX_FACTORIAL_ARG:
        raise CalculatorError(
            f"factorial поддерживается до {MAX_FACTORIAL_ARG} — такой расчёт не выполняется"
        )


def _apply(
    func: Callable[..., Any],
    *args: Any,
    name: str | None = None,
) -> int | float:
    label = f"«{name}»" if name else "выражения"
    try:
        result = func(*args)
    except ZeroDivisionError as exc:
        raise CalculatorError("деление на ноль невозможно") from exc
    except ValueError as exc:
        raise CalculatorError(f"аргумент вне области определения {label}: {exc}") from exc
    except OverflowError as exc:
        raise CalculatorError(f"результат слишком велик для вычисления ({exc})") from exc
    except TypeError as exc:
        raise CalculatorError(f"неверные аргументы {label}: {exc}") from exc
    if isinstance(result, bool) or not isinstance(result, (int, float)):
        raise CalculatorError(f"результат {label} не является числом")
    if isinstance(result, float) and math.isnan(result):
        raise CalculatorError("результат не определён (NaN)")
    if isinstance(result, float) and math.isinf(result):
        raise CalculatorError("результат бесконечен")
    return result
