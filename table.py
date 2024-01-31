#!/usr/bin/env python3

import sys

from error import TableError, error_fmt
from parser import Expr, Stmt, UnaryOp, BinOp, parse_stmt
from lexer import Lexer, TokenType


def usage():
    print("USAGE: table <file>")


def print_ast(ast: Stmt | Expr | UnaryOp | BinOp, indent=0):
    # Special case for binary and unary operators
    if isinstance(ast, (UnaryOp, BinOp)):
        print(f"{' ' * indent}{type(ast).__name__}: {ast._name_}")
        return

    # Print class name
    print(f"{' ' * indent}{type(ast).__name__}:")

    # Print fields
    indent += 4
    for key, val in ast.__dict__.items():
        if isinstance(val, list):
            print(f"{' ' * indent}{key}:")
            for item in val:
                print_ast(item, indent + 4)
        elif "__dict__" in dir(val):
            print_ast(val, indent)
        else:
            print(f"{' ' * indent}{key}: {val}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(error_fmt("ERROR: Incorrect number of arguments"))
        usage()
        exit(1)

    filename = sys.argv[1]
    lexer = Lexer(filename)
    try:
        stmt = parse_stmt(lexer)
        print_ast(stmt)

        # Make sure no input is remaining
        if (tok := lexer.next_token().typ) != TokenType.EOF:
            raise TableError(f"Unexpected trailing input: {tok}")

        # print(stmts)

    except TableError as e:
        print(e)
        exit(1)
