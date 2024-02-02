#!/usr/bin/env python3

import sys

from error import TableError, error_fmt
from table_parser import parse_source_file
from lexer import Lexer
from table_ast import print_top_level


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
        # stmt = parse_stmt(lexer)
        program = parse_source_file(lexer)
        for definition in program:
            print_top_level(definition)

    except TableError as e:
        print(e)
        exit(1)
