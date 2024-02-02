from __future__ import annotations
from enum import IntEnum, auto
from dataclasses import dataclass
from typing import assert_never


class BinOp(IntEnum):
    PLUS = auto()
    MINUS = auto()
    TIMES = auto()
    DIVIDE = auto()


@dataclass
class BinExpr:
    op: BinOp
    lhs: Expr
    rhs: Expr


class UnaryOp(IntEnum):
    DEREF = auto()  # *
    REF = auto()  # &
    NEGATE = auto()


@dataclass
class UnaryExpr:
    op: UnaryOp
    inner: Expr


@dataclass
class LiteralExpr:
    typ: TableType
    val: str


@dataclass
class FunCall:
    name: Expr
    args: list[Expr]


@dataclass
class IdentExpr:
    name: str


@dataclass
class NameExpr:
    """
    Expressions like std.io

    In this example, `std` is the name and `io` is the subname.
    """

    name: Expr
    subname: str


@dataclass
class AssignExpr:
    name: Expr
    value: Expr


type Expr = AssignExpr | BinExpr | UnaryExpr | LiteralExpr | FunCall | IdentExpr | NameExpr


class DefType(IntEnum):
    LET = auto()
    CONST = auto()


@dataclass
class TableArrayType:
    element_type: TableType
    length: int


@dataclass
class TablePointerType:
    points_to: TableType


@dataclass
class TableUserType:
    path: list[str]


type TableType = TableArrayType | TablePointerType | TableUserType | "int" | "float" | "str" | "none" | "Self"


@dataclass
class Binding:
    name: str
    typ: TableType


@dataclass
class LetDef:
    binding: Binding
    value: Expr


@dataclass
class ConstDef:
    binding: Binding
    value: Expr


@dataclass
class ExprStmt:
    expr: Expr


@dataclass
class BlockStmt:
    stmts: list[Stmt]


@dataclass
class ReturnStmt:
    value: Expr


type Stmt = LetDef | ConstDef | ExprStmt | BlockStmt | ReturnStmt


@dataclass
class Struct:
    name: str
    fields: list[Binding]
    methods: list[FunDef]


@dataclass
class Interface:
    name: str
    functions: list[tuple[str, FunSig]]


@dataclass
class FunSig:
    params: list[Binding]
    return_type: TableType


@dataclass
class FunDef:
    name: str
    sig: FunSig
    body: BlockStmt


@dataclass
class Import:
    path: list[str]


type TopLevel = ConstDef | FunDef | Import | Interface | Struct


def print_type(typ: TableType, indent: int = 0):
    match typ:
        case TableArrayType(inner, length):
            print(" " * indent + "ArrayType:")
            print_type(inner, indent + 4)
            print(" " * (indent + 4) + "length:", str(length))
        case TablePointerType(inner):
            print(" " * indent + "PointerType:")
            print_type(inner, indent + 4)
        case TableUserType(path):
            print(" " * indent + "UserType:" + ".".join(path))
        case "int":
            print(" " * indent + "IntType")
        case "float":
            print(" " * indent + "FloatType")
        case "str":
            print(" " * indent + "StrType")
        case "Self":
            print(" " * indent + "SelfType")
        case "none":
            print(" " * indent + "NoneType")
        case _:
            assert_never(typ)


def print_expr(expr: Expr, indent: int = 0):
    match expr:
        case AssignExpr(name, value):
            print(" " * indent + "AssignExpr:")
            print_expr(name, indent + 4)
            print_expr(value, indent + 4)
        case BinExpr(op, lhs, rhs):
            print(" " * indent + "BinaryExpr:")
            print(" " * (indent + 4) + "op:", op._name_)
            print_expr(lhs, indent + 4)
            print_expr(rhs, indent + 4)
        case UnaryExpr(op, data):
            print(" " * indent + "UnaryExpr:")
            print(" " * (indent + 4) + "op:", op._name_)
            print_expr(data, indent + 4)
        case LiteralExpr(typ, val):
            print(" " * indent + "LiteralExpr:")
            print_type(typ, indent + 4)
            print(" " * (indent + 4) + "value:", val)
        case FunCall(name, args):
            print(" " * indent + "FunCall:")
            print_expr(name, indent + 4)
            print(" " * (indent + 4) + "args:")
            for arg in args:
                print_expr(arg, indent + 8)
        case IdentExpr(name):
            print(" " * indent + "IdentExpr:", name)
        case NameExpr(name, subname):
            print(" " * indent + "NameExpr:")
            print_expr(name, indent + 4)
            print(" " * (indent + 4) + subname)
        case _:
            assert_never(expr)


def print_binding(binding: Binding, indent: int = 0):
    print(" " * indent + "Binding:")
    print(" " * (indent + 4) + binding.name)
    print_type(binding.typ, indent + 4)


def print_stmt(stmt: Stmt, indent: int = 0):
    match stmt:
        case LetDef(binding, value):
            print(" " * indent + "LetDef:")
            print_binding(binding, indent + 4)
            print_expr(value, indent + 4)
        case ConstDef(binding, value):
            print(" " * indent + "ConstDef:")
            print_binding(binding, indent + 4)
            print_expr(value, indent + 4)
        case ExprStmt(expr):
            print(" " * indent + "ExprStmt:")
            print_expr(expr, indent + 4)
        case BlockStmt(stmts):
            print(" " * indent + "BlockStmt:")
            for stmt in stmts:
                print_stmt(stmt, indent + 4)
        case ReturnStmt(value):
            print(" " * indent + "ReturnStmt:")
            print_expr(value, indent + 4)
        case _:
            assert_never(stmt)


# TopLevel = ConstDef | FunDef | Import | Interface | Struct
def print_top_level(defn: TopLevel, indent: int = 0):
    match defn:
        case ConstDef(binding, value):
            print(" " * indent + "ConstDef:")
            print_binding(binding, indent + 4)
            print_expr(value, indent + 4)
        case FunDef(name, sig, body):
            print(" " * indent + "FunDef:")
            print(" " * (indent + 4) + repr(sig))
            print_stmt(body, indent + 4)
        case Import(path):
            print(" " * indent + "Import: " + ".".join(path))
        case Interface(name, functions):
            print(" " * indent + "Interface:", name)
            for name, sig in functions:
                print(" " * (indent + 4) + name, sig)
        case Struct(name, fields, methods):
            print(" " * indent + "Struct:", name)
            for field in fields:
                print_binding(field, indent + 4)
            for fun in methods:
                print_top_level(fun, indent + 4)
        case _:
            assert_never(defn)
