from typing import Literal
from enum import IntEnum, auto
from dataclasses import dataclass


# Utilities
def error(msg: str):
    """Print msg in red and exit with code 1."""
    print("\033[1;32m" + msg + "\033[0m")
    exit(1)


def compiler_error(file: str, line: int, col: int, msg: str):
    """Print 'file: line.col: msg' in red and exit with code 1."""
    error(f"{file}: {line}.{col}: msg")


@dataclass
class Location:
    file: str
    posn: int
    line: int
    col: int


# Tokenize
class TokenType(IntEnum):
    EOF = auto()
    # Sequences of characters
    INT_LIT = auto()
    FLOAT_LIT = auto()
    STR_LIT = auto()
    IDENT = auto()
    # Symbols
    COMMA = auto()  # ,
    L_PAREN = auto()  # (
    R_PAREN = auto()  # )
    L_BRACK = auto()  # {
    R_BRACK = auto()  # }
    L_SQUARE = auto()  # [
    R_SQUARE = auto()  # ]
    L_ANGLE = auto()  # <
    R_ANGLE = auto()  # >
    DOT = auto()  # .
    PLUS = auto()  # +
    MINUS = auto()  # -
    TIMES = auto()  # *
    DIVIDE = auto()  # /
    EQUALS = auto()  # =
    DOUBLE_EQUALS = auto()  # ==
    # TODO: Implement the following:
    # PLUS_EQUALS = auto()
    # MINUS_EQUALS = auto()
    # TIMES_EQUALS = auto()
    # DIVIDE_EQUALS = auto()
    COLON = auto()
    SEMICOLON = auto()
    # Keywords
    IF = auto()
    ELSE = auto()
    FOR = auto()
    WHILE = auto()
    RET = auto()  # "ret" not "return"
    STRUCT = auto()
    FUN = auto()
    LET = auto()
    CONST = auto()
    INT = auto()  # "int"
    FLOAT = auto()  # "float"
    STR = auto()  # "str"


class Token:
    typ: TokenType
    loc: Location
    lexeme: str
    val: int | float | str | None

    def __init__(self, typ: TokenType, loc: Location, lexeme: str, value=None):
        self.typ = typ
        self.loc = loc
        self.lexeme = lexeme
        if value:
            self.value = value

    def __repr__(self):
        return f"{self.lexeme} : {self.loc.file}:{self.loc.line+1}.{self.loc.col+1}"


class Lexer:
    # Name of file
    filename: str
    # Program string
    contents: str
    # Current character
    current_char: str | Literal[False]
    # Current position in input string
    posn: int
    # Current line
    line: int
    # Beginning of line
    bol: int

    def __init__(self, filename: str):
        """Create a new lexer by reading from a file."""
        try:
            with open(filename, "r") as file:
                self.filename = filename
                self.contents = file.read()
                self.posn = 0
                self.line = 0
                self.bol = 0
                if len(self.contents) > 0:
                    self.current_char = self.contents[0]
                else:
                    self.current_char = False
        except FileNotFoundError:
            error(f"ERROR: Could not open file {filename}")

    def advance(self):
        """
        Advance the lexer by one character.
        """
        if not self.current_char:
            return
        elif self.contents[self.posn] == "\n":
            self.line += 1
            self.bol = self.posn + 1

        self.posn += 1

        # Set current_char to False if we are at end of input
        if len(self.contents) == self.posn:
            self.current_char = False
        else:
            self.current_char = self.contents[self.posn]

    def skip_whitespace(self):
        """Skip one block of whitespace."""
        while self.current_char and self.current_char.isspace():
            self.advance()

    def skip_comment(self):
        """Skip one comment."""
        while self.current_char and self.current_char != "\n":
            self.advance()

    def skip_whitespace_and_comments(self):
        """
        Skip many blocks of whitespace and comments until next char isn't
        whitespace or comment.
        """
        while self.current_char:
            if self.current_char.isspace():
                self.skip_whitespace()
            elif self.current_char == "#":
                self.skip_comment()
            else:
                break

    def consume_string(self, loc) -> Token:
        string = ""
        while self.current_char:
            if self.current_char == "\"":
                self.advance()
                break
            elif self.current_char == "\\":
                self.advance()
                match self.current_char:
                    case False:
                        assert False, "unexpected EOF"
                    case "a":
                        string += "\a"
                    case "b":
                        string += "\b"
                    case "f":
                        string += "\f"
                    case "n":
                        string += "\n"
                    case "r":
                        string += "\r"
                    case "t":
                        string += "\t"
                    case "v":
                        string += "\v"
                    case "\\":
                        string += "\\"
                    case "'":
                        string += "\'"
                    case "\"":
                        string += "\""
                    case _:
                        assert False, f"unexpected escaped character: \\{self.current_char}"
            else:
                string += self.current_char
            self.advance()
        return Token(TokenType.STR_LIT, loc, "\"" + string + "\"", string)

    def consume_number(self, loc) -> Token:
        num_str = ""
        while self.current_char and (self.current_char.isdigit() or self.current_char == "."):
            if self.current_char == ".":
                assert False, "not implemented: floating point literals"
            num_str += self.current_char
            self.advance()
        value = int(num_str)
        return Token(TokenType.INT_LIT, loc, num_str, value)

    def consume_ident(self, loc) -> Token:
        ident = ""
        while self.current_char and (self.current_char.isalnum() or self.current_char == "_"):
            ident += self.current_char
            self.advance()
        return Token(TokenType.IDENT, loc, ident, ident)

    def next_token(self) -> Token | Literal[False]:
        self.skip_whitespace_and_comments()

        loc = Location(self.filename, self.posn, self.line, self.posn - self.bol)

        if not self.current_char:
            return Token(TokenType.EOF, loc, "EOF")

        match self.contents[self.posn]:
            case ",":
                self.advance()
                return Token(TokenType.COMMA, loc, ",")
            case "(":
                self.advance()
                return Token(TokenType.L_PAREN, loc, "(")
            case ")":
                self.advance()
                return Token(TokenType.R_PAREN, loc, ")")
            case "{":
                self.advance()
                return Token(TokenType.L_BRACK, loc, "{")
            case "}":
                self.advance()
                return Token(TokenType.R_BRACK, loc, "}")
            case "[":
                self.advance()
                return Token(TokenType.L_SQUARE, loc, "[")
            case "]":
                self.advance()
                return Token(TokenType.R_SQUARE, loc, "]")
            case "<":
                self.advance()
                return Token(TokenType.L_ANGLE, loc, "<")
            case ">":
                self.advance()
                return Token(TokenType.R_ANGLE, loc, ">")
            case ":":
                self.advance()
                return Token(TokenType.COLON, loc, ":")
            case ";":
                self.advance()
                return Token(TokenType.SEMICOLON, loc, ";")
            case ".":
                self.advance()
                return Token(TokenType.DOT, loc, ".")
            case "+":
                self.advance()
                return Token(TokenType.PLUS, loc, "+")
            case "-":
                self.advance()
                return Token(TokenType.MINUS, loc, "+")
            case "*":
                self.advance()
                return Token(TokenType.TIMES, loc, "+")
            case "/":
                self.advance()
                return Token(TokenType.DIVIDE, loc, "+")
            case "=":
                self.advance()
                if self.current_char == "=":
                    self.advance()
                    return Token(TokenType.DOUBLE_EQUALS, loc, "==")
                else:
                    return Token(TokenType.EQUALS, loc, "=")
            case "\"":
                return self.consume_string(loc)
            case c if c.isdigit():
                return self.consume_number(loc)
            case c if c.isalpha() or c == "_":
                return self.consume_ident(loc)
            case _:
                assert False, "not implemented: literals, identifiers, keywords"

        return False


# Parse

# Compile


if __name__ == "__main__":
    # TODO: Read command line args
    lexer = Lexer("test_input.mini")
    while lexer.current_char:
        tok = lexer.next_token()
        print(tok)
