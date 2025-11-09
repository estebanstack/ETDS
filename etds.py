import sys

class TKind:
    ID = 'ID'
    NUM = 'NUM'
    PLUS = 'PLUS'
    MINUS = 'MINUS'
    TIMES = 'TIMES'
    DIV = 'DIV'
    LPAREN = 'LPAREN'
    RPAREN = 'RPAREN'
    EOF = 'EOF'

class Token:
    def __init__(self, clase, lexema, valor, linea, columna):
        self.clase = clase
        self.lexema = lexema   
        self.valor = valor     
        self.linea = linea
        self.columna = columna
    def __repr__(self):
        return "Token(%s,%r,%r,%d:%d)" % (self.clase, self.lexema, self.valor, self.linea, self.columna)


class Lexer:
    def __init__(self, texto):
        self.texto = texto
        self.i = 0
        self.linea = 1
        self.columna = 1
        self._EOF_CH = "\0"

    def _peek(self):
        if self.i < len(self.texto):
            return self.texto[self.i]
        return self._EOF_CH

    def _advance(self):
        ch = self._peek()
        if ch == "\n":
            self.linea += 1
            self.columna = 1
        else:
            self.columna += 1
        self.i += 1
        return ch

    def _consumir_id(self):
        inicio = self.i
        while True:
            ch = self._peek()
            if ch.isalnum() or ch == '_':
                self._advance()
            else:
                break
        return self.texto[inicio:self.i]

    def _consumir_num(self):
        inicio = self.i
        while self._peek().isdigit():
            self._advance()
        if self._peek() == '.':
            self._advance()
            if not self._peek().isdigit():
                raise SyntaxError("Punto decimal sin dígitos en %d:%d" % (self.linea, self.columna))
            while self._peek().isdigit():
                self._advance()
            lex = self.texto[inicio:self.i]
            try:
                val = float(lex)
            except Exception:
                raise SyntaxError("Número inválido %r en %d:%d" % (lex, self.linea, self.columna))
            return lex, val
        lex = self.texto[inicio:self.i]
        try:
            val = int(lex)
        except Exception:
            raise SyntaxError("Número inválido %r en %d:%d" % (lex, self.linea, self.columna))
        return lex, val

    def tokens(self):
        toks = []
        while True:
            ch = self._peek()
            if ch in " \t\r\n":
                self._advance()
                continue
            if ch == self._EOF_CH:
                toks.append(Token(TKind.EOF, '', None, self.linea, self.columna))
                break
            lin, col = self.linea, self.columna
            if ch.isalpha() or ch == '_':
                lex = self._consumir_id()
                toks.append(Token(TKind.ID, lex, lex, lin, col))
                continue
            if ch.isdigit():
                lex, val = self._consumir_num()
                toks.append(Token(TKind.NUM, lex, val, lin, col))
                continue
            if ch == '+':
                self._advance(); toks.append(Token(TKind.PLUS, '+', None, lin, col)); continue
            if ch == '-':
                self._advance(); toks.append(Token(TKind.MINUS, '-', None, lin, col)); continue
            if ch == '*':
                self._advance(); toks.append(Token(TKind.TIMES, '*', None, lin, col)); continue
            if ch == '/':
                self._advance(); toks.append(Token(TKind.DIV, '/', None, lin, col)); continue
            if ch == '(':
                self._advance(); toks.append(Token(TKind.LPAREN, '(', None, lin, col)); continue
            if ch == ')':
                self._advance(); toks.append(Token(TKind.RPAREN, ')', None, lin, col)); continue
            raise SyntaxError("Carácter inesperado %r en %d:%d" % (ch, lin, col))
        return toks


class AST: pass

class Bin(AST):
    def __init__(self, op, izq, der):
        self.op = op   # '+', '-', '*', '/'
        self.izq = izq
        self.der = der

class Id(AST):
    def __init__(self, nombre):
        self.nombre = nombre

class Num(AST):
    def __init__(self, valor):
        self.valor = valor

def imprimir_ast(nodo, prefijo="", es_ultimo=True):
    conector = "└── " if es_ultimo else "├── "
    if isinstance(nodo, Bin):
        print(prefijo + conector + nodo.op)
        # actualizar prefijo para los hijos
        nuevo_prefijo = prefijo + ("    " if es_ultimo else "│   ")
        hijos = [nodo.izq, nodo.der]
        for i, h in enumerate(hijos):
            imprimir_ast(h, nuevo_prefijo, i == len(hijos) - 1)
    elif isinstance(nodo, Id):
        print(prefijo + conector + f"Id({nodo.nombre})")
    elif isinstance(nodo, Num):
        print(prefijo + conector + f"Num({nodo.valor})")
    else:
        raise TypeError(f"Nodo AST desconocido: {type(nodo)}")


class EntradaTS:
    def __init__(self, nombre, clase, tipo, primera_linea, primera_columna):
        self.nombre = nombre
        self.clase = clase
        self.tipo = tipo
        self.primera_linea = primera_linea
        self.primera_columna = primera_columna

class TablaSimbolos:
    def __init__(self):
        self._tab = {}
    def insertar_si_ausente(self, nombre, linea, columna):
        if nombre not in self._tab:
            self._tab[nombre] = EntradaTS(nombre, 'VAR', 'number', linea, columna)
        return self._tab[nombre]
    def entradas(self):
        return list(self._tab.values())
    def __len__(self):
        return len(self._tab)


class Parser:
    def __init__(self, tokens):
        self.toks = tokens
        self.k = 0
        self.TS = TablaSimbolos()

    def _mirar(self):
        return self.toks[self.k]

    def _comer(self, clase):
        tok = self._mirar()
        if tok.clase != clase:
            raise SyntaxError("Se esperaba %s pero llegó %s en %d:%d" %
                              (clase, tok.clase, tok.linea, tok.columna))
        self.k += 1
        return tok


    def E(self):
        T_trad = self.T()               
        E_p_trad = self.E_p(T_trad)     
        return E_p_trad                 


    def E_p(self, th):
        tok = self._mirar()
        if tok.clase == TKind.PLUS or tok.clase == TKind.MINUS:
            op = '+' if tok.clase == TKind.PLUS else '-'
            self._comer(tok.clase)
            T_trad = self.T()
            combinado = Bin(op, th, T_trad)  
            return self.E_p(combinado)        
        elif tok.clase == TKind.RPAREN or tok.clase == TKind.EOF:
            return th                        
        else:
            raise SyntaxError("Token inesperado en E': %r" % (tok,))


    def T(self):
        F_trad = self.F()
        T_p_trad = self.T_p(F_trad)
        return T_p_trad


    def T_p(self, th):
        tok = self._mirar()
        if tok.clase == TKind.TIMES or tok.clase == TKind.DIV:
            op = '*' if tok.clase == TKind.TIMES else '/'
            self._comer(tok.clase)
            F_trad = self.F()
            combinado = Bin(op, th, F_trad)
            return self.T_p(combinado)
        elif tok.clase in (TKind.PLUS, TKind.MINUS, TKind.RPAREN, TKind.EOF):
            return th                         
        else:
            raise SyntaxError("Token inesperado en T': %r" % (tok,))

    
    def F(self):
        tok = self._mirar()
        if tok.clase == TKind.LPAREN:
            self._comer(TKind.LPAREN)
            E_trad = self.E()
            self._comer(TKind.RPAREN)
            return E_trad
        elif tok.clase == TKind.ID:
            t = self._comer(TKind.ID)
            self.TS.insertar_si_ausente(t.lexema, t.linea, t.columna)
            return Id(t.lexema)
        elif tok.clase == TKind.NUM:
            t = self._comer(TKind.NUM)
            return Num(t.valor)
        else:
            raise SyntaxError("Token inesperado en F: %r" % (tok,))


PRIMEROS = {
    'E':  ['(', 'id', 'num'],
    "E'": ['+', '-', 'ε'],
    'T':  ['(', 'id', 'num'],
    "T'": ['*', '/', 'ε'],
    'F':  ['(', 'id', 'num'],
}
SIGUIENTES = {
    'E':  [')', '$'],
    "E'": [')', '$'],
    'T':  ['+', '-', ')', '$'],
    "T'": ['+', '-', ')', '$'],
    'F':  ['*', '/', '+', '-', ')', '$'],
}


def compilar_y_mostrar(expr):
    print("\nEntrada")
    print(expr)
    lex = Lexer(expr)
    toks = lex.tokens()
    parser = Parser(toks)
    ast = parser.E()

    # Debe terminar en EOF
    if parser._mirar().clase != TKind.EOF:
        resto = parser._mirar()
        raise SyntaxError("Entrada no consumida; quedó %r" % (resto,))

    print("\nAST decorado")
    imprimir_ast(ast)

    print("\nTabla de simbolos")
    if len(parser.TS) == 0:
        print("<vacía>")
    else:
        for e in sorted(parser.TS.entradas(), key=lambda s: s.nombre):
            print("nombre=%s, clase=%s, tipo=%s, primera_vez=%d:%d" %
                  (e.nombre, e.clase, e.tipo, e.primera_linea, e.primera_columna))

if __name__ == '__main__':
        print("Analizador ETDS de expresiones aritmeticas ")
        expr = input("Ingresa una expresion: ")
        compilar_y_mostrar(expr)
