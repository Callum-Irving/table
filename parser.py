from __future__ import annotations
from enum import IntEnum, auto
from dataclasses import dataclass

from error import TableError
from lexer import Lexer, Token, TokenType

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


@dataclass
class LiteralExpr:
    val: int | float | str


@dataclass
class FunCall:
    name: Expr
    args: list[Expr]


@dataclass
class IdentExpr:
    name: str


@dataclass
class AssignExpr:
    name: Expr
    value: Expr


# union type for expression
Expr = AssignExpr | BinExpr | LiteralExpr | FunCall | IdentExpr


class DefStmt:
    let_or_const: bool  # False = let, True = const


@dataclass
class ExprStmt:
    expr: Expr


Stmt = DefStmt | ExprStmt


def parse_args(lexer: Lexer) -> list[Expr] | TableError:
    """Parse comma-separated list of expressions."""
    open_paren = lexer.expect_type(TokenType.L_PAREN)
    if isinstance(open_paren, TableError):
        return open_paren

    args = []

    while True:
        arg = parse_expr(lexer)
        if isinstance(arg, TableError):
            return arg
        else:
            args.append(arg)

        comma = lexer.peek()
        if isinstance(comma, TableError):
            return comma
        elif comma.typ != TokenType.COMMA:
            break
        else:
            comma = lexer.next_token()
            if isinstance(comma, TableError):
                return comma

    close_paren = lexer.expect_type(TokenType.R_PAREN)
    if isinstance(close_paren, TableError):
        return close_paren

    return args


def parse_name_expr(lexer: Lexer) -> Expr | TableError:
    """
    Parse a name expression.

    <nameexpr> ::= <ident> ("." <ident>)*
    """
    # TODO: Should also contain dereferences, pointer arithmatic, etc.
    # TODO: Just parsing a single ident for now
    name = lexer.expect_type(TokenType.IDENT)
    if isinstance(name, TableError):
        return name

    assert isinstance(name.val, str), "ident with non-str name"
    return IdentExpr(name.val)


def parse_factor(lexer: Lexer) -> Expr | TableError:
    """
    Parse a factor.

    <factor> ::= "(" <expr> ")" | <ident> | <num> | <str>
    """
    tok = lexer.peek()
    if isinstance(tok, TableError):
        return tok

    match tok.typ:
        case TokenType.L_PAREN:
            l_paren = lexer.next_token()
            if isinstance(l_paren, TableError):
                return l_paren

            expr = parse_expr(lexer)
            if isinstance(expr, TableError):
                return expr

            r_paren = lexer.expect_type(TokenType.R_PAREN)
            if isinstance(r_paren, TableError):
                return r_paren

            return expr
        case TokenType.IDENT:
            name = parse_name_expr(lexer)
            return name
            # if isinstance(name, TableError):
            #     return name
            #
            # Determines if name or function call
            # tok = lexer.peek()
            # if isinstance(tok, Token) and tok.typ == TokenType.L_PAREN:
            #     # Parse function call
            #     args = parse_args(lexer)
            #     if isinstance(args, TableError):
            #         return args
            #     return FunCall(name, args)
            # else:
            #     return name
        case TokenType.INT_LIT:
            tok = lexer.next_token()
            if isinstance(tok, TableError):
                return tok
            assert isinstance(tok.val, int), "int literal with non-int value"
            return LiteralExpr(tok.val)
        case other:
            return TableError(f"Unexpected token: {other!r}", tok.loc)


def parse_unary(lexer: Lexer) -> Expr | TableError:
    # TODO: implement
    return parse_factor(lexer)


def parse_funcall(lexer: Lexer) -> Expr | TableError:
    """
    Parse function call.

    <funcall> ::= <unary> <args> | <unary>
    """
    # TODO: use funcall ::= <unary> (<args>)* to support calling a function
    # returned by another function
    # Example: retfun()()
    func_name = parse_unary(lexer)
    if isinstance(func_name, TableError):
        return func_name

    next_tok = lexer.peek()
    if isinstance(next_tok, TableError):
        return next_tok
    elif next_tok.typ == TokenType.L_PAREN:
        args = parse_args(lexer)
        if isinstance(args, TableError):
            return args
        return FunCall(func_name, args)
    else:
        return func_name


def parse_term(lexer: Lexer) -> Expr | TableError:
    """
    Parse a term.

    <term> ::= <factor> (("*" | "/") <factor>)*
    """
    factor = parse_funcall(lexer)
    if isinstance(factor, TableError):
        return factor

    next_tok = lexer.peek()
    if isinstance(next_tok, TableError):
        return next_tok

    while next_tok.typ == TokenType.STAR or next_tok.typ == TokenType.DIVIDE:
        plus_or_minus = lexer.next_token()
        if isinstance(plus_or_minus, TableError):
            return plus_or_minus

        next_factor = parse_funcall(lexer)
        if isinstance(next_factor, TableError):
            return next_factor

        op = None
        if plus_or_minus.typ == TokenType.STAR:
            op = BinOp.TIMES
        elif plus_or_minus == TokenType.DIVIDE:
            op = BinOp.DIVIDE
        else:
            assert False, "unreachable"

        factor = BinExpr(op, factor, next_factor)

    return factor


def parse_addexpr(lexer: Lexer) -> Expr | TableError:
    """
    Parse an addition expression.

    <addexpr> ::= <term> (("+" | "-") <term>)*
    """
    term = parse_term(lexer)
    if isinstance(term, TableError):
        return term

    next_tok = lexer.peek()
    if isinstance(next_tok, TableError):
        return next_tok

    while next_tok.typ == TokenType.PLUS or next_tok.typ == TokenType.MINUS:
        plus_or_minus = lexer.next_token()
        if isinstance(plus_or_minus, TableError):
            return plus_or_minus

        next_term = parse_term(lexer)
        if isinstance(next_term, TableError):
            return next_term

        op = None
        if plus_or_minus.typ == TokenType.PLUS:
            op = BinOp.PLUS
        elif plus_or_minus == TokenType.MINUS:
            op = BinOp.MINUS
        else:
            assert False, "unreachable"

        term = BinExpr(op, term, next_term)
        next_tok = lexer.peek()
        if isinstance(next_tok, TableError):
            return next_tok

    return term


def parse_expr(lexer: Lexer) -> Expr | TableError:
    """
    Parse an expression.

    <expr> ::= <assign> | <addexpr>
    <assign> ::= <addexpr> "=" <addexpr>
    """
    first_expr = parse_addexpr(lexer)
    if isinstance(first_expr, TableError):
        return first_expr

    tok = lexer.peek()
    if isinstance(tok, TableError) or tok.typ != TokenType.EQUALS:
        return first_expr
    else:
        # Assignment expression
        equals = lexer.next_token()
        assert isinstance(equals, Token), "should not error"

        value = parse_addexpr(lexer)
        if isinstance(value, TableError):
            return value

        return AssignExpr(first_expr, value)


def parse_def(lexer: Lexer) -> Stmt | TableError:
    """
    Parse a definition statement.

    <def_stmt> ::= ("let" | "const") <ident> ":" <type> "=" <expr> ";"
    """
    assert False, "not implemented: parse def stmt"


def parse_stmt(lexer: Lexer) -> Stmt | TableError:
    """
    Parse a single statement.

    <stmt> ::= <def_stmt> | <const_stmt> | <expr_stmt>
    """
    next_tok = lexer.peek()
    if isinstance(next_tok, TableError):
        return next_tok

    if next_tok.typ == TokenType.LET:
        assert False, "not implemented: let def"
    elif next_tok.typ == TokenType.CONST:
        assert False, "not implemented: const def"
    else:
        expr = parse_expr(lexer)
        if isinstance(expr, TableError):
            return expr

        semicolon = lexer.expect_type(TokenType.SEMICOLON)
        if isinstance(semicolon, TableError):
            return semicolon

        return ExprStmt(expr)


def parse_stmt_list(lexer: Lexer) -> list[Stmt] | TableError:
    """
    Parse a list of statements.

    <stmts> ::= <stmt>*
    """
    open_brack = lexer.expect_type(TokenType.L_BRACK)
    if isinstance(open_brack, TableError):
        return open_brack

    stmts = []
    next_tok = lexer.peek()
    while True:
        if isinstance(next_tok, TableError):
            return next_tok
        elif next_tok.typ == TokenType.R_BRACK:
            break

        stmt = parse_stmt(lexer)
        if isinstance(stmt, TableError):
            return stmt
        stmts.append(stmt)
        next_tok = lexer.peek()

    return stmts
