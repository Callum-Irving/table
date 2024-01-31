from __future__ import annotations
from enum import IntEnum, auto
from dataclasses import dataclass

from error import TableError
from lexer import Lexer, TokenType


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
    typ: TableTypeEnum
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


# union type for expression
type Expr = AssignExpr | BinExpr | UnaryExpr | LiteralExpr | FunCall | IdentExpr | NameExpr


class DefType(IntEnum):
    LET = auto()
    CONST = auto()


@dataclass
class TableType:
    typ: TableTypeEnum
    # For user-defined types only:
    value: list[str] | None = None


class TableTypeEnum(IntEnum):
    INT = auto()
    FLOAT = auto()
    STR = auto()
    NONE = auto()
    USER_DEFINED = auto()


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


type Stmt = LetDef | ConstDef | ExprStmt | BlockStmt


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


def parse_args(lexer: Lexer) -> list[Expr]:
    """Parse comma-separated list of expressions, surrounded by parantheses.

    ``<args> ::= "(" (<expr> ("," <expr>)*)? ")"``

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: A list of parsed expressions.
    
    .. warning:: Mutates lexer.
    """
    # Expect open paren
    _ = lexer.expect_type(TokenType.L_PAREN)

    args = []

    # Special case when argument list is empty
    if lexer.peek().typ == TokenType.R_PAREN:
        _ = lexer.expect_type(TokenType.R_PAREN)
        return args

    # Parse first argument
    first_arg = parse_expr(lexer)
    args.append(first_arg)

    # Parse the rest of the arguments
    while lexer.peek().typ == TokenType.COMMA:
        _ = lexer.expect_type(TokenType.COMMA)
        arg = parse_expr(lexer)
        args.append(arg)

    # Expect close paren
    _ = lexer.expect_type(TokenType.R_PAREN)

    return args


def parse_factor(lexer: Lexer) -> Expr:
    """Parse a factor.

    ``<factor> ::= "(" <expr> ")" | <ident> | <num> | <str>``

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: An expression.
    
    .. warning:: Mutates lexer.
    """
    tok = lexer.next_token()

    match tok.typ:
        case TokenType.L_PAREN:
            expr = parse_expr(lexer)
            _ = lexer.expect_type(TokenType.R_PAREN)  # expect close paren
            return expr
        case TokenType.IDENT:
            assert isinstance(tok.val, str), "token val should be str"
            return IdentExpr(tok.val)
        case TokenType.INT_LIT:
            assert tok.val, "int literal value should be a string"
            return LiteralExpr(TableTypeEnum.INT, tok.val)
        case TokenType.FLOAT_LIT:
            assert tok.val, "float literal value should be a string"
            return LiteralExpr(TableTypeEnum.FLOAT, tok.val)
        case TokenType.STR_LIT:
            assert tok.val, "string literal value should be a string"
            return LiteralExpr(TableTypeEnum.STR, tok.val)
        case _:
            raise TableError(
                f"Unexpected token when parsing factor: {tok.lexeme}", tok.loc
            )


def parse_name_expr(lexer: Lexer) -> Expr:
    """Parse a name expression.

    ``<name_expr> ::= <factor> ("." <ident>)*``

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: An expression.
    
    .. warning:: Mutates lexer.
    """
    expr = parse_factor(lexer)
    while lexer.peek().typ == TokenType.DOT:
        _ = lexer.expect_type(TokenType.DOT)
        ident = lexer.expect_type(TokenType.IDENT)
        assert isinstance(ident.val, str), "ident val should be str"
        expr = NameExpr(expr, ident.val)

    return expr


def parse_unary(lexer: Lexer) -> Expr:
    """Parse a unary expression.

    ``<unary> ::= ("&" | "*") <name_expr>``

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: An expression.
    
    .. warning:: Mutates lexer.
    """
    # TODO: code is repetitive
    next_tok = lexer.peek()
    if next_tok.typ == TokenType.AMPERSAND:
        _ = lexer.expect_type(TokenType.AMPERSAND)
        inner = parse_name_expr(lexer)
        return UnaryExpr(UnaryOp.REF, inner)
    elif next_tok.typ == TokenType.STAR:
        _ = lexer.expect_type(TokenType.STAR)
        inner = parse_name_expr(lexer)
        return UnaryExpr(UnaryOp.DEREF, inner)
    elif next_tok.typ == TokenType.MINUS:
        _ = lexer.expect_type(TokenType.MINUS)
        inner = parse_name_expr(lexer)
        return UnaryExpr(UnaryOp.NEGATE, inner)
    else:
        return parse_name_expr(lexer)


def parse_funcall(lexer: Lexer) -> Expr:
    """Parse a function call.

    ``<funcall> ::= <unary> (<args>)*``

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: An expression.
    
    .. warning:: Mutates lexer.
    """
    expr = parse_unary(lexer)

    while lexer.peek().typ == TokenType.L_PAREN:
        args = parse_args(lexer)
        expr = FunCall(expr, args)

    return expr


def parse_term(lexer: Lexer) -> Expr:
    """Parse a term.

    ``<term> ::= <funcall> (("*" | "/") <funcall>)*``

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: An expression.
    
    .. warning:: Mutates lexer.
    """
    factor = parse_funcall(lexer)

    while lexer.peek().typ == TokenType.STAR or lexer.peek().typ == TokenType.DIVIDE:
        plus_or_minus = lexer.next_token()
        next_factor = parse_funcall(lexer)

        op = None
        if plus_or_minus.typ == TokenType.STAR:
            op = BinOp.TIMES
        else:
            op = BinOp.DIVIDE

        factor = BinExpr(op, factor, next_factor)

    return factor


def parse_addexpr(lexer: Lexer) -> Expr:
    """Parse an addition expression.

    ``<addexpr> ::= <term> (("+" | "-") <term>)*``

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: An expression.
    
    .. warning:: Mutates lexer.
    """
    term = parse_term(lexer)

    while lexer.peek().typ == TokenType.PLUS or lexer.peek().typ == TokenType.MINUS:
        plus_or_minus = lexer.next_token()

        next_term = parse_term(lexer)

        op = None
        if plus_or_minus.typ == TokenType.PLUS:
            op = BinOp.PLUS
        elif plus_or_minus == TokenType.MINUS:
            op = BinOp.MINUS
        else:
            assert False, "unreachable"

        term = BinExpr(op, term, next_term)

    return term


def parse_expr(lexer: Lexer) -> Expr:
    """Parse an expression.

    ``<expr> ::= <assign> | <addexpr>
    <assign> ::= <addexpr> "=" <addexpr>``

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: An expression.
    
    .. warning:: Mutates lexer.
    """
    first_expr = parse_addexpr(lexer)

    tok = lexer.peek()
    if tok.typ != TokenType.EQUALS:
        return first_expr
    else:
        # Assignment expression
        _ = lexer.expect_type(TokenType.EQUALS)
        value = parse_addexpr(lexer)
        return AssignExpr(first_expr, value)


def parse_type_name(lexer: Lexer) -> TableType:
    """Parse a type name.

    ``<type> ::= "int" | "float" | "str" | <ident> ("." <ident>)*``

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: A TableType representing the parsed type name.
    
    .. warning:: Mutates lexer.
    """
    tok = lexer.next_token()
    if tok.typ == TokenType.INT:
        return TableType(TableTypeEnum.INT)
    elif tok.typ == TokenType.FLOAT:
        return TableType(TableTypeEnum.FLOAT)
    elif tok.typ == TokenType.STR:
        return TableType(TableTypeEnum.STR)
    elif tok.typ == TokenType.IDENT:
        assert isinstance(tok.val, str), "ident value must be string"
        path = [tok.val]
        while lexer.peek().typ == TokenType.DOT:
            _ = lexer.expect_type(TokenType.DOT)
            ident = lexer.expect_type(TokenType.IDENT)
            assert isinstance(ident.val, str), "ident value must be string"
            path.append(ident.val)
        return TableType(TableTypeEnum.USER_DEFINED, path)
    else:
        raise TableError(f"Expected type or ident, found {tok.lexeme}", tok.loc)


def parse_binding(lexer: Lexer) -> Binding:
    """Parse a binding.

    ``<binding> ::= <ident> ":" <type>
    <type> ::= "int" | "float" | "str"``

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: A binding.
    
    .. warning:: Mutates lexer.
    """
    name = lexer.expect_type(TokenType.IDENT)
    _ = lexer.expect_type(TokenType.COLON)
    binding_type = parse_type_name(lexer)
    assert isinstance(name.val, str), "ident value must be string"
    return Binding(name.val, binding_type)


def parse_let_def(lexer: Lexer) -> LetDef:
    """Parse a let definition.

    ``<let_def> ::= "let" <binding> "=" <expr> ";"``

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: A let definition.
    
    .. warning:: Mutates lexer.
    """
    _ = lexer.expect_type(TokenType.LET)
    binding = parse_binding(lexer)
    _ = lexer.expect_type(TokenType.EQUALS)
    value = parse_expr(lexer)
    _ = lexer.expect_type(TokenType.SEMICOLON)
    return LetDef(binding, value)


def parse_const_def(lexer: Lexer) -> ConstDef:
    """Parse a const definition.

    ``<const_def> ::= "const" <binding> "=" <expr> ";"``

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: A const definition.
    
    .. warning:: Mutates lexer.
    """
    _ = lexer.expect_type(TokenType.CONST)
    binding = parse_binding(lexer)
    _ = lexer.expect_type(TokenType.EQUALS)
    value = parse_expr(lexer)
    _ = lexer.expect_type(TokenType.SEMICOLON)
    return ConstDef(binding, value)


def parse_block_stmt(lexer: Lexer) -> BlockStmt:
    """Parse a block statement.

    ``<block_stmt> ::= "{" <stmt>* "}"``

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: A block statement.
    
    .. warning:: Mutates lexer.
    """
    # Expect open bracket
    _ = lexer.expect_type(TokenType.L_BRACK)

    stmts = []
    while lexer.peek().typ != TokenType.R_BRACK:
        stmt = parse_stmt(lexer)
        stmts.append(stmt)

    # Expect close bracket
    _ = lexer.expect_type(TokenType.R_BRACK)

    return BlockStmt(stmts)


def parse_stmt(lexer: Lexer) -> Stmt:
    """Parse a statement.

    ``<stmt> ::= <let_def> | <const_def> | <block_stmt> | <expr_stmt>``

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: A statement.
    
    .. warning:: Mutates lexer.
    """
    next_tok = lexer.peek()

    if next_tok.typ == TokenType.LET:
        return parse_let_def(lexer)
    elif next_tok.typ == TokenType.CONST:
        return parse_const_def(lexer)
    elif next_tok.typ == TokenType.L_BRACK:
        return parse_block_stmt(lexer)
    else:
        expr = parse_expr(lexer)
        # Expect semicolon to end statement
        _ = lexer.expect_type(TokenType.SEMICOLON)
        return ExprStmt(expr)


def parse_params(lexer: Lexer) -> list[Binding]:
    """Parse comma-separated list of bindings, surrounded by parentheses.

    ``<params> ::= "(" (<binding> ("," <binding>)*)? ")"``

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: A list of bindings.
    
    .. warning:: Mutates lexer.
    """
    # Expect open paren
    _ = lexer.expect_type(TokenType.L_PAREN)

    params = []

    # Special case when argument list is empty
    if lexer.peek().typ == TokenType.R_PAREN:
        _ = lexer.expect_type(TokenType.R_PAREN)
        return params

    # Parse first parameter
    first_arg = parse_binding(lexer)
    params.append(first_arg)

    # Parse the rest of the arguments
    while lexer.peek().typ == TokenType.COMMA:
        _ = lexer.expect_type(TokenType.COMMA)
        param = parse_binding(lexer)
        params.append(param)

    # Expect close paren
    _ = lexer.expect_type(TokenType.R_PAREN)

    return params


def parse_fun_def(lexer: Lexer) -> FunDef:
    """Parse a function definition.

    ``<fun_def> ::= <named_fun_sig> <block_stmt>``

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: A function definition.
    
    .. warning:: Mutates lexer.
    """
    name, sig = parse_named_fun_sig(lexer)

    body = parse_block_stmt(lexer)
    assert isinstance(body, BlockStmt), "parse_block_stmt returns BlockStmt"

    return FunDef(name, sig, body)


def parse_import(lexer: Lexer) -> Import:
    """Parse an import.

    ``<import> ::= "import" <ident> ("." <ident>)* ";"``

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: An import.
    
    .. warning:: Mutates lexer.
    """
    _ = lexer.expect_type(TokenType.IMPORT)
    first_seg = lexer.expect_type(TokenType.IDENT)
    assert isinstance(first_seg.val, str), "ident value must be string"
    path = [first_seg.val]

    while lexer.peek().typ == TokenType.DOT:
        _ = lexer.expect_type(TokenType.DOT)
        next_seg = lexer.expect_type(TokenType.IDENT)
        assert isinstance(next_seg.val, str), "ident_value must be string"
        path.append(next_seg.val)

    _ = lexer.expect_type(TokenType.SEMICOLON)
    return Import(path)


def parse_named_fun_sig(lexer: Lexer) -> tuple[str, FunSig]:
    """Parse the start of a function definition or declaration.

    <named_fun_sig> ::= "fun" <ident> <params> (":" <type>)?

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: A tuple containg function name and signature.

    .. warning:: Mutates lexer.
    """
    _ = lexer.expect_type(TokenType.FUN)
    name = lexer.expect_type(TokenType.IDENT)
    assert isinstance(name.val, str), "ident value must be string"

    # TODO: Parse generics here

    params = parse_params(lexer)
    return_type = TableType(TableTypeEnum.NONE)
    if lexer.peek().typ == TokenType.COLON:
        _ = lexer.expect_type(TokenType.COLON)
        return_type = parse_type_name(lexer)
    sig = FunSig(params, return_type)

    return (name.val, sig)


def parse_fun_decl(lexer: Lexer) -> tuple[str, FunSig]:
    """Parse a function declaration.

    ``<fun_decl> ::= <named_fun_sig> ";"

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: A tuple containg function name and signature.

    .. warning:: Mutates lexer.
    """
    sig = parse_named_fun_sig(lexer)
    _ = lexer.expect_type(TokenType.SEMICOLON)
    return sig


def parse_interface(lexer: Lexer) -> Interface:
    """Parse an interface definition.

    ``<interface> ::= "interface" <ident> "{" <fun_decl>+ "}"``

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: An interface definition.

    .. warning:: Mutates lexer.
    """
    _ = lexer.expect_type(TokenType.INTERFACE)
    name = lexer.expect_type(TokenType.IDENT)
    assert isinstance(name.val, str), "ident value must be string"
    _ = lexer.expect_type(TokenType.L_BRACK)

    functions = []
    while lexer.peek().typ != TokenType.R_BRACK:
        fun_decl = parse_fun_decl(lexer)
        functions.append(fun_decl)

    r_brack = lexer.expect_type(TokenType.R_BRACK)
    if len(functions) == 0:
        raise TableError("Expected at least one function declaration", r_brack.loc)

    return Interface(name.val, functions)


def parse_struct(lexer: Lexer) -> Struct:
    assert False, "not implemented: parse struct"


def parse_top_level(lexer: Lexer) -> TopLevel:
    """Parse a top-level definition or import.

    ``<top_level> ::= <const_def> | <fundef> | <import>``

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: A top-level definition or import.
    
    .. warning:: Mutates lexer.
    """
    tok = lexer.peek()
    if tok.typ == TokenType.CONST:
        return parse_const_def(lexer)
    elif tok.typ == TokenType.FUN:
        return parse_fun_def(lexer)
    elif tok.typ == TokenType.IMPORT:
        return parse_import(lexer)
    elif tok.typ == TokenType.INTERFACE:
        return parse_interface(lexer)
    elif tok.typ == TokenType.STRUCT:
        return parse_struct(lexer)
    else:
        raise TableError(
            f"Expected const or fun to begin top-level definition, found: {tok.lexeme}",
            tok.loc,
        )


def parse_source_file(lexer: Lexer) -> list[TopLevel]:
    """Parse a list of top-level definitions or imports.

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: A list of top-level definitions or imports.

    .. warning:: Mutates lexer.
    """
    defs = []
    while lexer.peek().typ != TokenType.EOF:
        definition = parse_top_level(lexer)
        defs.append(definition)
    return defs
