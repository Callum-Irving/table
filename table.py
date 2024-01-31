#!/usr/bin/env python3

import sys

from error import TableError, error_fmt
from parser import parse_stmt
from lexer import Lexer


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
        print(stmts)
    except TableError as e:
        print(repr(e))
