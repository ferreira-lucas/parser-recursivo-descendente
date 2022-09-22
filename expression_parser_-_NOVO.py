"""Implement a simple expression evaluator parses."""

# For easier connection with class examples, we use names such as E or T_prime.
# pylint: disable=invalid-name

# Language definition:
#
# E = TE'
# E' = +TE' | - TE' | &
# T = FT'
# T' = * FT' | / FT' | &
# F = ( E ) | num
# num = [+-]?([0-9]+(.[0-9]+)?|.[0-9]+)(e[0-9]+)+)?)

import math
import re

SYMBOL_TABLE = {
    "cos": {"type": "method", "value": "var = cos"},
    "sin": {"type": "method", "value": "var = sin"},
}

""" variavel responsavel por trazer o resultado do methodo exec()"""
_locals = {}


def cos(value):
    """methodo fixo para calcular coseno"""
    return math.cos(value)


def sin(value):
    """methodo fixo para calcular seno"""
    return math.sin(value)


def addSymbol(symbol):
    """adiciona token e tipo na tabela de simbolos Obs. value = None"""
    SYMBOL_TABLE[symbol["token"]] = symbol["data"]


def addValue(token, value):
    """adiciona o valor ao simbolo existente na tabela"""
    SYMBOL_TABLE[token]["value"] = value


def getSymbolData(token):
    """Captura o valor existente na tabela"""
    return SYMBOL_TABLE[token]


class Lexer:
    """Implements the expression lexer."""

    OPEN_PAR = 1
    CLOSE_PAR = 2
    OPERATOR = 3
    ID = 4
    NUM = 5
    _EQUAL = 6

    def __init__(self, data):
        """Initialize object."""
        self.data = data
        self.current = 0
        self.previous = -1
        self.num_re = re.compile(r"[+-]?(\d+(\.\d*)?|\.\d+)(e\d+)?")
        self.variable = re.compile(r"[a-zA-Z][a-zA-Z0-9]*")

    def __iter__(self):
        """Start the lexer iterator."""
        self.current = 0
        return self

    def error(self, msg=None):
        err = (
            f"Error at {self.current}: "
            f"{self.data[self.current - 1:self.current + 10]}"
        )
        if msg is not None:
            err = f"{msg}\n{err}"
        raise Exception(err)

    def put_back(self):
        self.current = self.previous

    def lookAhead(self, data):
        """funcao responsavel por executar um next() retornando as informacoes do proximo com a garantia que será
        mantido o valor atual do current (necessario quando precisamos olhar mais de uma casa a frente)"""

        previous = self.previous
        current = self.current
        token, value = next(data)
        self.current = current
        self.previous = previous
        return (token, value)

    def __next__(self):
        """Retrieve the next token."""
        if self.current < len(self.data):
            while self.data[self.current] in " \t\n\r":
                self.current += 1
            self.previous = self.current
            char = self.data[self.current]
            self.current += 1
            if char == "=":
                return (Lexer._EQUAL, char)
            if char == "(":
                return (Lexer.OPEN_PAR, char)
            if char == ")":
                return (Lexer.CLOSE_PAR, char)
            # Do not handle minus operator.
            if char in "+/*^":
                return (Lexer.OPERATOR, char)
            match = self.num_re.match(self.data[self.current - 1 :])
            if match is None:
                # If there is no match we may have a minus operator

                if char == "-":
                    return (Lexer.OPERATOR, char)
                # verifica se é uma variavel
                match = self.variable.match(self.data[self.current - 1 :])
                if match is not None:
                    self.current += match.end() - 1

                    # tenta adicionar na tabela de sibolos
                    new_symbol = {
                        "token": match.group().replace(" ", ""),
                        "data": {"type": "variable", "value": None},
                    }

                    if new_symbol["token"] not in SYMBOL_TABLE.keys():
                        addSymbol(new_symbol)

                    return (Lexer.ID, match.group().replace(" ", ""))
                # If we get here, there is an error an unexpected char.
                raise Exception(
                    f"Error at {self.current}: "
                    f"{self.data[self.current - 1:self.current + 10]}"
                )

            self.current += match.end() - 1
            return (Lexer.NUM, match.group().replace(" ", ""))
        raise StopIteration()


def parse_P(data):
    """Parse an Expression P."""
    S = parse_S(data)
    P_prime = parse_P_prime(data)
    return S if P_prime is None else S + P_prime


def parse_P_prime(data):
    """Parse an Expression P'."""
    try:
        token, value = next(data)
    except StopIteration:
        return None
    if value is not None:
        S = parse_S(data)
        P_prime = parse_P_prime(data)
        return S if P_prime is None else S + P_prime
    data.put_back()
    return None


def parse_S(data):
    """Parse an Expression S."""

    try:
        token, identifier = next(data)
    except StopIteration:
        return 0
    if token == Lexer.ID:
        # pega as informacoes que existem na tabela de simbolos
        _data = getSymbolData(identifier)

        # varifica se já foi atribuido valor a esse simbolo
        if _data["type"] == "variable" and _data["value"] is None:

            try:
                token, equal = next(data)
            except StopIteration:
                return 0
            if equal != "=":
                data.error(f"Unexpected token: '{equal}'.")
            try:
                token, value = next(data)
            except StopIteration:
                return 0
            data.put_back()
            # adiciona valor na tabela de simbolos
            addValue(identifier, value)

            return 0

    data.put_back()
    E = parse_E(data)
    return E


def parse_E(data):
    """Parse an expression E."""
    T = parse_T(data)
    E_prime = parse_E_prime(data)
    return T if E_prime is None else T + E_prime


def parse_E_prime(data):
    """Parse an expression E'."""
    try:
        token, operator = next(data)
    except StopIteration:
        return None
    if token == Lexer.OPERATOR:
        if operator not in "+-":
            data.error(f"Unexpected token: '{operator}'.")
        T = parse_T(data)
        # We don't need the result of the recursion,
        # only the recuscion itself
        _E_prime = parse_E_prime(data)  # noqa
        return T if operator == "+" else -1 * T
    data.put_back()
    return None


def parse_T(data):
    """Parse an expression T."""
    F = parse_F(data)
    T_prime = parse_T_prime(data)
    return F if T_prime is None else F * T_prime


def parse_T_prime(data):
    """Parse an expression T'."""
    try:
        token, operator = next(data)
    except StopIteration:
        return None
    if token == Lexer.OPERATOR and operator in "*/":
        F = parse_F(data)
        # We don't need the result of the recursion,
        # only the recuscion itself
        _T_prime = parse_T_prime(data)  # noqa
        return F if operator == "*" else 1 / F
    data.put_back()
    return None


def parse_F(data):

    G = parse_G(data)
    F_prime = parse_F_prime(data)

    return G if F_prime is None else G**F_prime


def parse_F_prime(data):
    try:
        token, operator = next(data)
    except StopIteration:
        return None
    if token == Lexer.OPERATOR:
        x, y = data.lookAhead(data)
        # verifica se o operador representa uma potencia
        if operator == "^" or (operator == "*" and y == "*"):
            # se o simbolo for ** anda pra frente
            if y == "*":
                next(data)

            G = parse_G(data)
            _F_prime = parse_F_prime(data)  # noqa
            return G if (operator == "^" or operator == "*") else None
        data.put_back()
        return None

    data.put_back()
    return None


def parse_G(data):
    """Parse an expression G."""

    try:
        token, value = next(data)
    except StopIteration:
        raise Exception("Unexpected end of source.") from None
    if token == Lexer.OPEN_PAR:
        E = parse_E(data)
        if next(data) != (Lexer.CLOSE_PAR, ")"):
            data.error("Unbalanced parenthesis.")
        return E
    if token == Lexer.NUM:
        return float(value)
    if token == Lexer.ID:
        # caso for uma ID volta uma casa e executa parse x
        data.put_back()
        X = parse_X(data)
        return X

    raise data.error(f"Unexpected token: {value}.")


def parse_X(data):
    try:
        token, value = next(data)
    except StopIteration:
        return 1
    # captura o valor do simbolo
    _data = getSymbolData(value)

    # caso seja uma variavel retorna o valor dela
    if _data["type"] == "variable":

        _value = _data["value"]
        if _value is None:
            _value = 0

        return float(_value)

    # se for um methodo executa o mesmo
    if _data["type"] == "method":

        A = parse_A(data)

        _method = _data["value"] + "(" + str(A) + ")"
        # funcao externa para executar string
        exec(_method, None, _locals)
        return float(_locals["var"])

    raise data.error(f"Unexpected token: {value}.")


def parse_A(data):
    try:
        token, value = next(data)

    except StopIteration:
        raise Exception("Unexpected end of source.") from None
    if token == Lexer.OPEN_PAR:
        E = parse_E(data)
        if next(data) != (Lexer.CLOSE_PAR, ")"):
            data.error("Unbalanced parenthesis.")
        return E

    return None


def parse(source_code):
    """Parse the source code."""
    lexer = Lexer(source_code)
    return parse_P(lexer)


if __name__ == "__main__":

    expressions = [
        ("x = 2 y = 3 x + y", 2 + 3),
        ("cos(3)", math.cos(3)),
        ("5 * 4", 5 * 4),
        ("10 / 2", 10 / 2),
        ("5 ^ 5", 5**5),
        ("5 ** 5", 5**5),
        ("4 * 4 + 3 ** 3", 4 * 4 + 3**3),
        ("1 + 1", 1 + 1),
        ("2 * 3", 2 * 3),
        ("5 / 4", 5 / 4),
        ("2 * 3 + 1", 2 * 3 + 1),
        ("1 + 2 * 3", 1 + 2 * 3),
        ("(2 * 3) + 1", (2 * 3) + 1),
        ("2 * (3 + 1)", 2 * (3 + 1)),
        ("(2 + 1) * 3", (2 + 1) * 3),
        ("-2 + 3", -2 + 3),
        ("5 + (-2)", 5 + (-2)),
        ("5 * -2", 5 * -2),
        ("-1 - -2", -1 - -2),
        ("-1 - 2", -1 - 2),
        ("4 - 5", 4 - 5),
        ("1 - 2", 1 - 2),
        ("3 - ((8 + 3) * -2)", 3 - ((8 + 3) * -2)),
        ("2.01e2 - 200", 2.01e2 - 200),
        ("2*3*4", 2 * 3 * 4),
        ("2 + 3 + 4 * 3 * 2 + 2", 2 + 3 + 4 * 3 * 2 * 2),
        ("10 + 11", 10 + 11),
    ]

    for expression, expected in expressions:
        result = "PASS" if parse(expression) == expected else "FAIL"
        print(f"Expression: {expression} - {result}")
