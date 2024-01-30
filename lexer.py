from enum import IntEnum, auto
from error import TableError, Location, error_fmt


# Tokenize
class TokenType(IntEnum):
    # Sequences of characters
    INT_LIT = auto()
    FLOAT_LIT = auto()
    STR_LIT = auto()
    IDENT = auto()
    # Symbols
    L_PAREN = auto()  # (
    R_PAREN = auto()  # )
    L_BRACK = auto()  # {
    R_BRACK = auto()  # }
    L_SQUARE = auto()  # [
    # ]You decided to cancel logging in to our site using one of your existing accounts. If this was a mistake, please proceed to sign-in.
    R_SQUARE = auto()
    L_ANGLE = auto()  # <
    R_ANGLE = auto()  # >
    DOT = auto()  # .
    COMMA = auto()  # ,
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
    # TODO: Add bitwise
    COLON = auto()  # :
    SEMICOLON = auto()  # ;
    STAR = auto()  # *
    APOSTROPHE = auto()  # '
    EOF = auto()
    # Keywords
    IF = auto()  # if
    ELSE = auto()  # else
    FOR = auto()  # for
    WHILE = auto()  # while
    RETURN = auto()  # return
    STRUCT = auto()  # struct
    FUN = auto()  # fun
    LET = auto()  # let
    CONST = auto()  # const
    INT = auto()  # int
    FLOAT = auto()  # float
    STR = auto()  # str

    def __repr__(self):
        return self._name_


# Builtin types
type_token = TokenType.INT | TokenType.FLOAT | TokenType.STR


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
            self.val = value

    def __repr__(self):
        return f"{self.lexeme} [{self.typ!r}] : {self.loc!r}"


class Lexer:
    # Name of file
    filename: str
    # Program string
    contents: str
    # Current character
    current_char: str | None
    # Current location
    loc: Location
    # Used for peek
    read_tokens: list

    def __init__(self, filename: str):
        """Create a new lexer by reading from a file."""
        try:
            with open(filename, "r") as file:
                self.filename = filename
                self.contents = file.read()
                self.loc = Location(filename, 0, 0, 0)
                # self.posn = 0
                # self.line = 0
                # self.bol = 0
                self.read_tokens = []
                if len(self.contents) > 0:
                    self.current_char = self.contents[0]
                else:
                    self.current_char = None
        except FileNotFoundError:
            print(error_fmt(f"ERROR: Could not open file {filename}"))
            exit(1)

    def advance(self):
        """
        Advance the lexer by one character.
        """
        if not self.current_char:
            return
        elif self.contents[self.loc.posn] == "\n":
            self.loc.line += 1
            self.loc.col = -1  # TODO: kind of a hack

        self.loc.posn += 1
        self.loc.col += 1

        # Set current_char to False if we are at end of input
        if len(self.contents) == self.loc.posn:
            self.current_char = None
        else:
            self.current_char = self.contents[self.loc.posn]

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

    def consume_string(self, loc) -> Token | TableError:
        string = ""
        if self.current_char != '"':
            assert False, "unreachable"

        self.advance()

        while self.current_char:
            if self.current_char == '"':
                self.advance()
                break
            elif self.current_char == "\\":
                self.advance()
                match self.current_char:
                    case False:
                        return TableError("Unexpected EOF", self.loc)
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
                        string += "'"
                    case '"':
                        string += '"'
                    case "e":
                        string += "\033"
                    case _:
                        return TableError(
                            f"Unknown escaped character: \\{self.current_char}",
                            self.loc,
                        )
            else:
                string += self.current_char
            self.advance()
        return Token(TokenType.STR_LIT, loc, '"' + string + '"', string)

    def consume_number(self, loc) -> Token:
        num_str = ""
        while self.current_char and (
            self.current_char.isdigit() or self.current_char == "."
        ):
            if self.current_char == ".":
                assert False, "not implemented: floating point literals"
            num_str += self.current_char
            self.advance()
        value = int(num_str)
        return Token(TokenType.INT_LIT, loc, num_str, value)

    def consume_ident(self, loc) -> Token:
        ident = ""
        while self.current_char and (
            self.current_char.isalnum() or self.current_char == "_"
        ):
            ident += self.current_char
            self.advance()
        return Token(TokenType.IDENT, loc, ident, ident)

    def next_token(self) -> Token | TableError:
        if len(self.read_tokens) > 0:
            return self.read_tokens.pop(0)

        self.skip_whitespace_and_comments()

        loc = self.loc.copy()

        if not self.current_char:
            return Token(TokenType.EOF, loc, "EOF")

        match self.contents[self.loc.posn]:
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
                return Token(TokenType.MINUS, loc, "-")
            case "*":
                self.advance()
                return Token(TokenType.TIMES, loc, "*")
            case "/":
                self.advance()
                return Token(TokenType.DIVIDE, loc, "/")
            case "=":
                self.advance()
                if self.current_char == "=":
                    self.advance()
                    return Token(TokenType.DOUBLE_EQUALS, loc, "==")
                else:
                    return Token(TokenType.EQUALS, loc, "=")
            case '"':
                return self.consume_string(loc)
            case "*":
                self.advance()
                return Token(TokenType.STAR, loc, "*")
            case c if c.isdigit():
                return self.consume_number(loc)
            case c if c.isalpha() or c == "_":
                return self.consume_ident(loc)
            case _:
                assert False, "not implemented: unexpected char error"

    def peek(self) -> Token | TableError:
        if len(self.read_tokens) > 0:
            return self.read_tokens[0]
        else:
            tok = self.next_token()
            self.read_tokens.append(tok)
            return tok

    def expect_type(self, typ: TokenType) -> Token | TableError:
        """
        Advances the lexer by one token. If the token matches typ, it returns
        the token. Otherwise, it returns a TableError.
        """
        tok = self.next_token()
        if isinstance(tok, TableError):
            return tok

        if tok.typ != typ:
            return TableError(
                f"Expected token {typ!r}, found token {tok.typ!r}", tok.loc
            )
        else:
            return tok
