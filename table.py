#!/usr/bin/env python3

import sys

from error import TableError, error_fmt
from parser import parse_stmt
from lexer import Lexer, TokenType


def usage():
    print("USAGE: table <file>")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(error_fmt("ERROR: Incorrect number of arguments"))
        usage()
        exit(1)

    filename = sys.argv[1]
    lexer = Lexer(filename)
    try:
        stmts = parse_stmt(lexer)

        # Make sure no input is remaining
        if (tok := lexer.next_token().typ) != TokenType.EOF:
            raise TableError(f"Unexpected trailing input: {tok}")

        print(stmts)
    except TableError as e:
        print(e)
        exit(1)
