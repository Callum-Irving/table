#!/usr/bin/env python3

import sys

from error import error_fmt
from parser import parse_stmt_list
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
    stmts = parse_stmt_list(lexer)
    print(stmts)
