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

from lib2to3.pgen2.token import EQUAL
import re
import math



SYMBOL_TABLE = {'cos': {'type':'method', 'value': 'var = cos'},'sin': {'type':'method', 'value': 'var = sin'}}
_locals = {}

def cos(value):
    return math.cos(value)

def sin(value):
    return math.sin(value)

def addSymbol(symbol):
    """ adiciona token e tipo na tabela de simbolos"""
    SYMBOL_TABLE[symbol['token']] = symbol['data']
  
def addValue(token, symbol):
    """ adiciona o valor ao simbolo existente na tabela"""
    SYMBOL_TABLE[token]["value"] = symbol

def getSymbolData(token):
    """ Captura o valor existente na tabela """
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
                
                match = self.variable.match(self.data[self.current - 1 :])
                if match is not None:
                    self.current += match.end() - 1
                    """ TENTA ADICIONAR O METODO addSymbol"""
                    new_symbol = {'token':match.group().replace(" ", ""), 'data': {'type':'variable', 'value': None}}

                    if new_symbol['token'] not in SYMBOL_TABLE.keys():
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
    return S if P_prime is None else S * P_prime

def parse_P_prime(data):
    """Parse an Expression P'."""
    try:
        token, value = next(data)
    except StopIteration:
        return None
    if value is not None:
        S = parse_S(data)
        P_prime  = parse_P_prime(data)
        return S if P_prime is None else S + P_prime
    data.put_back()
    return None

def parse_S(data):
    """Parse an Expression S."""

    """ SE O PROXIMO FOR '=' CHAMA O METODO addValue"""
    try:
        token, identifier = next(data)
    except StopIteration:
        return 0
    if token == Lexer.ID:
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
        addValue(identifier,parse_E(data))
        print(SYMBOL_TABLE)
    
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

    return G if F_prime is None else G ** F_prime

def parse_F_prime(data):
    try:
        token, operator = next(data)
    except StopIteration:
        return None
    if token == Lexer.OPERATOR:
        if operator not in "^":
            data.put_back()
            return None
        G = parse_G(data)
        _F_prime = parse_F_prime(data)  # noqa
        return G if operator == "^" else None
        
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

        data.put_back()
        X = parse_X(data)
        return X

    raise data.error(f"Unexpected token: {value}.")

def parse_X(data):
    try:
        token, value = next(data)
    except StopIteration:
        return 1
    _data = getSymbolData(value)
    
    if _data['type'] == 'variable':
        
        _value = _data['value']
        return float(_value)

    if _data['value'] == 'method':

        data.put_back()
        
        
        E = parse_E(data)
        #### TESTES ####
        _method = _data['value']+"("+str(E)+")"
        exec(_method, None, _locals)
        return float(_locals['var'])
        
    raise data.error(f"Unexpected token: {value}.")
    

def parse_A(data):
    try:
        token, value = next(data)
    except StopIteration:
        return 1
    _data = getSymbolData(value)
    
    return 1

def parse(source_code):
    """Parse the source code."""
    lexer = Lexer(source_code)
    return parse_P(lexer)


if __name__ == "__main__":
    expressions = [
        "1 + 1",
        "x = 10 x + (9 + 7)",
        "cos(3)",
        "4 ^ 4"
    

    
    ]
    for expression in expressions:
        print(f"Expression: {expression}\t Result: {parse(expression)}")
