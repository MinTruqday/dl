import re

from sympy import Abs, Float, Integer, Rational, Symbol, cos, exp, log, simplify, sin, sqrt, tan
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)


ALLOWED_FUNCTIONS = {
    "abs": Abs,
    "cos": cos,
    "exp": exp,
    "log": log,
    "sin": sin,
    "sqrt": sqrt,
    "tan": tan,
}
TRANSFORMATIONS = standard_transformations + (convert_xor, implicit_multiplication_application)


def parse_symbolic(value: str):
    text = value.strip()
    if (
        not text
        or len(text) > 500
        or not re.fullmatch(r"[\w\s+\-*/^().,]+", text, flags=re.UNICODE)
    ):
        raise ValueError("symbolic_expression_invalid")
    names = set(re.findall(r"[^\W\d]\w*", text, flags=re.UNICODE))
    local_dict = {name: ALLOWED_FUNCTIONS.get(name.casefold(), Symbol(name)) for name in names}
    return parse_expr(
        text,
        local_dict=local_dict,
        global_dict={
            "Abs": Abs,
            "Float": Float,
            "Integer": Integer,
            "Rational": Rational,
            "Symbol": Symbol,
        },
        transformations=TRANSFORMATIONS,
        evaluate=True,
    )


def symbolic_equivalent(actual: str, expected: str):
    if actual.strip().casefold() == expected.strip().casefold():
        return True
    try:
        return simplify(parse_symbolic(actual) - parse_symbolic(expected)) == 0
    except Exception:
        return False
