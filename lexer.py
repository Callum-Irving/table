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
    STAR = auto()  # *
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
    AMPERSAND = auto()  # &
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

    def __str__(self):
        return self._name_


# Map of keyword strings to tokens
KEYWORD_DICT = {
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "for": TokenType.FOR,
    "while": TokenType.WHILE,
    "return": TokenType.RETURN,
    "struct": TokenType.STRUCT,
    "fun": TokenType.FUN,
    "let": TokenType.LET,
    "const": TokenType.CONST,
    "int": TokenType.INT,
    "float": TokenType.FLOAT,
    "str": TokenType.STR,
}


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

    def __str__(self):
        return f"{self.lexeme} [{self.typ}] : {self.loc}"


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
    peek_token: Token | None

    def __init__(self, filename: str):
        """Create a new lexer by reading from a file.

        Args:
            filename: The name of the file to read from.

        Mutates:
            self: Populates fields.
        """
        try:
            with open(filename, "r") as file:
                self.filename = filename
                self.contents = file.read()
                self.loc = Location(filename, 0, 0, 0)
                self.peek_token = None
                if len(self.contents) > 0:
                    self.current_char = self.contents[0]
                else:
                    self.current_char = None
        except FileNotFoundError:
            print(error_fmt(f"ERROR: Could not open file {filename}"))
            exit(1)

    def advance(self):
        """Advance the lexer by one character.

        Mutates:
            self: Advances the lexer position.
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
        """Skip one block of whitespace.

        Mutates:
            self: Advances the lexer position.
        """
        while self.current_char and self.current_char.isspace():
            self.advance()

    def skip_comment(self):
        """Skip one comment.

        Mutates:
            self: Advances the lexer position.
        """
        while self.current_char and self.current_char != "\n":
            self.advance()

    def skip_whitespace_and_comments(self):
        """Skip many blocks of whitespace and comments until next char isn't
        whitespace or comment.

        Mutates:
            self: Advances the lexer position.
        """
        while self.current_char:
            if self.current_char.isspace():
                self.skip_whitespace()
            elif self.current_char == "#":
                self.skip_comment()
            else:
                break

    def consume_string(self, loc) -> Token:
        """Consume a string literal from self.

        Args:
            loc: The location of the start of the string.

        Mutates:
            self: Advances the lexer position

        Returns:
            The string literal Token.

        Raises:
            TableError: If there is an unexpected EOF.
        """
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
                        raise TableError("Unexpected EOF", self.loc)
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
                        raise TableError(
                            f"Unknown escaped character: \\{self.current_char}",
                            self.loc,
                        )
            else:
                string += self.current_char
            self.advance()
        return Token(TokenType.STR_LIT, loc, '"' + string + '"', string)

    def consume_number(self, loc) -> Token:
        """Consume an integer or float literal from self.

        Args:
            loc: The starting location of the literal.

        Mutates:
            self: Advances the lexer position.

        Returns:
            The integer or float literal Token.
        """
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
        """Consume an identifier from self.

        Args:
            loc: The starting location of the identifier.

        Mutates:
            self: Advances the lexer.

        Returns:
            The identifier Token.
        """
        ident = ""
        while self.current_char and (
            self.current_char.isalnum() or self.current_char == "_"
        ):
            ident += self.current_char
            self.advance()

        # Check if ident is keyword
        if ident in KEYWORD_DICT:
            return Token(KEYWORD_DICT[ident], loc, ident, ident)
        else:
            return Token(TokenType.IDENT, loc, ident, ident)

    def next_token(self) -> Token:
        """Return the next token from self, advancing the lexer.

        Mutates:
            self: Advances the lexer position.

        Returns:
            The next token or EOF if there is none.

        Raises:
            TableError: If there is an unexpected character.
        """
        if self.peek_token:
            tok = self.peek_token
            self.peek_token = None
            return tok

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
                return Token(TokenType.STAR, loc, "*")
            case "&":
                self.advance()
                return Token(TokenType.AMPERSAND, loc, "&")
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
            case c if c.isdigit():
                return self.consume_number(loc)
            case c if c.isalpha() or c == "_":
                return self.consume_ident(loc)
            case _:
                assert False, "not implemented: unexpected char error"

    def peek(self) -> Token:
        """Returns the next token in self without advancing the lexer.

        Mutates:
            self: Modifies a field used for peeking.

        Returns:
            The next token from input.

        Raises:
            TableError: Raised if next_token raises an error.
        """
        # TODO: No need for a list
        if self.peek_token:
            return self.peek_token
        else:
            tok = self.next_token()
            self.peek_token = tok
            return tok

    def expect_type(self, typ: TokenType) -> Token:
        """Advance lexer by one token, raising error if token is unexpected.

        Advances the lexer by one token. If the token matches typ, it returns
        the token. Otherwise, it raises a TableError.

        Args:
            typ: The TokenType that the next token must match.

        Mutates:
            self: Advances the lexer position.

        Returns:
            The next token from self.

        Raises:
            TableError: If the next token does not match typ.
        """
        tok = self.next_token()

        if tok.typ != typ:
            raise TableError(f"Expected token {typ}, found token {tok.typ}", tok.loc)
        else:
            return tok
