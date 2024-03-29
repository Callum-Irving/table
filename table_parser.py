from __future__ import annotations

# TODO: Get rid of wildcard import
import table_ast
from error import TableError
from lexer import Lexer, TokenType


def parse_args(lexer: Lexer) -> list[table_ast.Expr]:
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


def parse_array_literal(lexer: Lexer) -> table_ast.ArrayExpr:
    assert False, "not implemented"


def parse_factor(lexer: Lexer) -> table_ast.Expr:
    """Parse a factor.

    ``<factor> ::= "(" <expr> ")" | <array> | <ident> | <num> | <str>
    <array> ::= "[" (<expr> ("," <expr>)*)? "]"``


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
        case TokenType.L_SQUARE:
            if lexer.peek().typ == TokenType.R_SQUARE:
                _ = lexer.expect_type(TokenType.R_SQUARE)
                return table_ast.ArrayExpr(list())
            items = [parse_expr(lexer)]
            while lexer.peek().typ == TokenType.COMMA:
                _ = lexer.expect_type(TokenType.COMMA)
                items.append(parse_expr(lexer))
            _ = lexer.expect_type(TokenType.R_SQUARE)
            return table_ast.ArrayExpr(items)
        case TokenType.IDENT:
            assert isinstance(tok.val, str), "token val should be str"
            return table_ast.IdentExpr(tok.val)
        case TokenType.INT_LIT:
            assert tok.val, "int literal value should be a string"
            return table_ast.IntExpr(tok.val)
        case TokenType.FLOAT_LIT:
            assert tok.val, "float literal value should be a string"
            return table_ast.FloatExpr(tok.val)
        case TokenType.STR_LIT:
            assert tok.val, "string literal value should be a string"
            return table_ast.StrExpr(tok.val)
        case _:
            raise TableError(
                f"Unexpected token when parsing factor: {tok.lexeme}", tok.loc
            )


def parse_name_expr(lexer: Lexer) -> table_ast.Expr:
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
        expr = table_ast.NameExpr(expr, ident.val)

    return expr


def parse_unary(lexer: Lexer) -> table_ast.Expr:
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
        return table_ast.UnaryExpr(table_ast.UnaryOp.REF, inner)
    elif next_tok.typ == TokenType.STAR:
        _ = lexer.expect_type(TokenType.STAR)
        inner = parse_name_expr(lexer)
        return table_ast.UnaryExpr(table_ast.UnaryOp.DEREF, inner)
    elif next_tok.typ == TokenType.MINUS:
        _ = lexer.expect_type(TokenType.MINUS)
        inner = parse_name_expr(lexer)
        return table_ast.UnaryExpr(table_ast.UnaryOp.NEGATE, inner)
    else:
        return parse_name_expr(lexer)


def parse_funcall(lexer: Lexer) -> table_ast.Expr:
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
        expr = table_ast.FunCall(expr, args)

    return expr


def parse_term(lexer: Lexer) -> table_ast.Expr:
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
            op = table_ast.BinOp.TIMES
        else:
            op = table_ast.BinOp.DIVIDE

        factor = table_ast.BinExpr(op, factor, next_factor)

    return factor


def parse_addexpr(lexer: Lexer) -> table_ast.Expr:
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
            op = table_ast.BinOp.PLUS
        elif plus_or_minus == TokenType.MINUS:
            op = table_ast.BinOp.MINUS
        else:
            assert False, "unreachable"

        term = table_ast.BinExpr(op, term, next_term)

    return term


def parse_expr(lexer: Lexer) -> table_ast.Expr:
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
        return table_ast.AssignExpr(first_expr, value)


def parse_type(lexer: Lexer) -> table_ast.TableType:
    """Parse a type name.

    ``<type> ::= "[" <type> ";" <int> "]" | "*" <type> | <ident> ("." <ident>)* | "Self" | "int" | "float" | "str"``

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: A TableType representing the parsed type name.

    .. warning:: Mutates lexer.
    """
    tok = lexer.next_token()
    if tok.typ == TokenType.L_SQUARE:
        inner = parse_type(lexer)
        _ = lexer.expect_type(TokenType.SEMICOLON)
        length = lexer.expect_type(TokenType.INT_LIT)
        try:
            length = int(length)
        except Exception:
            assert False, "handle exception"
        _ = lexer.expect_type(TokenType.R_SQUARE)
        return table_ast.TableArrayType(inner, length)
    elif tok.typ == TokenType.STAR:
        inner = parse_type(lexer)
        return table_ast.TablePointerType(inner)
    elif tok.typ == TokenType.SELF:
        return "Self"
    elif tok.typ == TokenType.INT:
        return "int"
    elif tok.typ == TokenType.FLOAT:
        return "float"
    elif tok.typ == TokenType.STR:
        return "str"
    elif tok.typ == TokenType.IDENT:
        assert isinstance(tok.val, str), "ident value must be string"
        path = [tok.val]
        while lexer.peek().typ == TokenType.DOT:
            _ = lexer.expect_type(TokenType.DOT)
            ident = lexer.expect_type(TokenType.IDENT)
            assert isinstance(ident.val, str), "ident value must be string"
            path.append(ident.val)
        return table_ast.TableUserType(path)
    else:
        raise TableError(f"Expected type or ident, found {tok.lexeme}", tok.loc)


def parse_binding(lexer: Lexer) -> table_ast.Binding:
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
    binding_type = parse_type(lexer)
    assert isinstance(name.val, str), "ident value must be string"
    return table_ast.Binding(name.val, binding_type)


def parse_let_def(lexer: Lexer) -> table_ast.LetDef:
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
    return table_ast.LetDef(binding, value)


def parse_const_def(lexer: Lexer) -> table_ast.ConstDef:
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
    return table_ast.ConstDef(binding, value)


def parse_block_stmt(lexer: Lexer) -> table_ast.BlockStmt:
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

    return table_ast.BlockStmt(stmts)


def parse_return_stmt(lexer: Lexer) -> table_ast.ReturnStmt:
    """Parse a return statement.

    ``<return_stmt> ::= "return" <expr> ";"

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: A return statement.

    .. warning:: Mutates lexer.
    """
    _ = lexer.expect_type(TokenType.RETURN)
    value = parse_expr(lexer)
    _ = lexer.expect_type(TokenType.SEMICOLON)
    return table_ast.ReturnStmt(value)


def parse_stmt(lexer: Lexer) -> table_ast.Stmt:
    """Parse a statement.

    ``<stmt> ::= <let_def> | <const_def> | <block_stmt> | <expr_stmt> | <return_stmt>``

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
    elif next_tok.typ == TokenType.RETURN:
        return parse_return_stmt(lexer)
    else:
        expr = parse_expr(lexer)
        # Expect semicolon to end statement
        _ = lexer.expect_type(TokenType.SEMICOLON)
        return table_ast.ExprStmt(expr)


def parse_params(lexer: Lexer) -> list[table_ast.Binding]:
    """Parse comma-separated list of bindings, surrounded by parentheses.

    ``<params> ::= "(" "self"? (<binding> ("," <binding>)*)? ")"``

    Note: This grammar doesn't show that a comma can follow self, but only if
    there is another parameter after.

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: A list of bindings.

    .. warning:: Mutates lexer.
    """
    # Expect open paren
    _ = lexer.expect_type(TokenType.L_PAREN)

    params = []

    # Optionally, take self parameter
    tok = lexer.peek()
    # TODO: This triple condition is not nice!
    if tok.typ == TokenType.IDENT and isinstance(tok.val, str) and tok.val == "self":
        _ = lexer.expect_type(TokenType.IDENT)
        params.append(table_ast.Binding(tok.val, "Self"))
        # Handle comma after self
        # TODO: Nesting not nice either!
        if lexer.peek().typ == TokenType.COMMA:
            _ = lexer.expect_type(TokenType.COMMA)
            if lexer.peek().typ == TokenType.R_PAREN:
                raise TableError("Unexpected trailing comma", lexer.peek().loc)

    # Special case when argument list is empty or just contains self
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


def parse_fun_def(lexer: Lexer) -> table_ast.FunDef:
    """Parse a function definition.

    ``<fun_def> ::= <named_fun_sig> <block_stmt>``

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: A function definition.

    .. warning:: Mutates lexer.
    """
    name, sig = parse_named_fun_sig(lexer)

    body = parse_block_stmt(lexer)
    assert isinstance(body, table_ast.BlockStmt), "parse_block_stmt returns BlockStmt"

    return table_ast.FunDef(name, sig, body)


def parse_import(lexer: Lexer) -> table_ast.Import:
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
    return table_ast.Import(path)


def parse_named_fun_sig(lexer: Lexer) -> tuple[str, table_ast.FunSig]:
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
    return_type = "none"
    if lexer.peek().typ == TokenType.COLON:
        _ = lexer.expect_type(TokenType.COLON)
        return_type = parse_type(lexer)
    sig = table_ast.FunSig(params, return_type)

    return (name.val, sig)


def parse_fun_decl(lexer: Lexer) -> tuple[str, table_ast.FunSig]:
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


def parse_interface(lexer: Lexer) -> table_ast.Interface:
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

    return table_ast.Interface(name.val, functions)


def parse_struct(lexer: Lexer) -> table_ast.Struct:
    """Parse a struct definition.

    ``<struct> ::= "struct" <ident> "{" (<struct_binding> | <fun_def>)+ "}"``

    :param lexer: The lexer to parse from.
    :raises TableError: Raised if parsing fails.
    :returns: A struct definition.

    .. warning:: Mutates lexer.
    """
    _ = lexer.expect_type(TokenType.STRUCT)
    name = lexer.expect_type(TokenType.IDENT)
    assert isinstance(name.val, str), "ident value must be string"
    _ = lexer.expect_type(TokenType.L_BRACK)

    fields = []
    methods = []
    while (tok := lexer.peek()).typ != TokenType.R_BRACK:
        if tok.typ == TokenType.IDENT:
            # parse binding (struct field)
            field = parse_binding(lexer)
            _ = lexer.expect_type(TokenType.SEMICOLON)
            fields.append(field)
        elif tok.typ == TokenType.FUN:
            # parse function (struct method)
            fun_def = parse_fun_def(lexer)
            methods.append(fun_def)
        else:
            raise TableError(
                f"Expected binding or function definition, found {tok.lexeme}", tok.loc
            )
    _ = lexer.expect_type(TokenType.R_BRACK)

    return table_ast.Struct(name.val, fields, methods)


def parse_top_level(lexer: Lexer) -> table_ast.TopLevel:
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


def parse_source_file(lexer: Lexer) -> list[table_ast.TopLevel]:
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
