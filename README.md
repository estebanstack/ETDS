# ETDS para una GIC de Expresiones Aritméticas  

---

## 1. Diseño de la Gramática GIC

**Gramática LL(1):**
```
E  → T E'
E' → + T E' | - T E' | ε
T  → F T'
T' → * F T' | / F T' | ε
F  → ( E ) | id | num
```

*Implementada en las funciones:*  
- `Parser.E()`  
- `Parser.E_p()`  
- `Parser.T()`  
- `Parser.T_p()`  
- `Parser.F()`

Cada no terminal corresponde a una funcion del parser (recursivo descendente LL(1)).

---

## 2. Definición de los Atributos

Atributos usados:
- **Heredado (`th`)** → pasa la subexpresión parcial acumulada.
- **Sintetizado (`trad`)** → devuelve el resultado (nodo del AST).

Tokens (`id`, `num`) tienen atributos:
- `id.lexema`
- `num.valor`

*Implementado en el código mediante:*
- Parámetros de las funciones `E_p(th)` y `T_p(th)`  
- Retorno de las funciones (`return ...`) equivale a `trad`.

---

## 3. Conjuntos de Primeros, Siguientes y Prediccion

**PRIMEROS**
```
PRIMEROS(E)  = { (, id, num }
PRIMEROS(E') = { +, -, ε }
PRIMEROS(T)  = { (, id, num }
PRIMEROS(T') = { *, /, ε }
PRIMEROS(F)  = { (, id, num }
```

**SIGUIENTES**
```
SIGUIENTES(E)  = { ), $ }
SIGUIENTES(E') = { ), $ }
SIGUIENTES(T)  = { +, -, ), $ }
SIGUIENTES(T') = { +, -, ), $ }
SIGUIENTES(F)  = { *, /, +, -, ), $ }
```

**PREDICCION**
```
- `E  → T E'` : { '(', id, num }
- `E' → + T E'` : { '+' }
- `E' → - T E'` : { '-' }
- `E' → ε`      : { ')', $ } (SIGUIENTES(E'))
- `T  → F T'` : { '(', id, num }
- `T' → * F T'` : { '*' }
- `T' → / F T'` : { '/' }
- `T' → ε`      : { '+', '-', ')', $ } (SIGUIENTES(T'))
- `F  → ( E )` : { '(' }
- `F  → id`    : { id }
- `F  → num`   : { num }

```

---

## 4. Generación del AST Decorado

El AST se genera durante el análisis sintáctico con las acciones semánticas.  
Los tipos de nodo son:
- `Bin(op, izq, der)` para operadores binarios
- `Id(nombre)`
- `Num(valor)`

*Creación de nodos en el código:*
- En `E_p()` y `T_p()` → `combinado = Bin(op, th, T_trad)`
- En `F()` → `return Id(t.lexema)` o `return Num(t.valor)`

*Impresión del AST:*
```python
└── +
    ├── Id(a)
    └── /
        ├── *
        │   ├── Num(3)
        │   └── Id(b)
        └── -
            ├── Num(4)
            └── Id(c)
```

---

## 5. Generación de la Tabla de Símbolos

Cada identificador (`id`) se registra una única vez con su posición en el código fuente.

*Estructuras:*
```python
class EntradaTS:
    nombre, clase, tipo, primera_linea, primera_columna
class TablaSimbolos:
    insertar_si_ausente(nombre, linea, columna)
```

*Llenado de la TS:*  
En la producción `F → id`:
```python
self.TS.insertar_si_ausente(t.lexema, t.linea, t.columna)
```

*Impresión:*
```python
Tabla de símbolos
nombre=a, clase=VAR, tipo=number, primera_vez=1:1
nombre=b, clase=VAR, tipo=number, primera_vez=1:9
nombre=c, clase=VAR, tipo=number, primera_vez=1:18
```

---

## 6. Gramática de Atributos

```
E  → T E'
     { E'.th  := T.trad;
       E.trad := E'.trad; }

E' → + T E'₁
     { E'₁.th := Bin('+', E'.th, T.trad);
       E'.trad:= E'₁.trad; }
   | - T E'₁
     { E'₁.th := Bin('-', E'.th, T.trad);
       E'.trad:= E'₁.trad; }
   | ε
     { E'.trad:= E'.th; }

T  → F T'
     { T'.th  := F.trad;
       T.trad := T'.trad; }

T' → * F T'₁
     { T'₁.th := Bin('*', T'.th, F.trad);
       T'.trad:= T'₁.trad; }
   | / F T'₁
     { T'₁.th := Bin('/', T'.th, F.trad);
       T'.trad:= T'₁.trad; }
   | ε
     { T'.trad:= T'.th; }

F  → ( E )
     { F.trad := E.trad; }
   | id
     { TS.insertar(id.lexema);
       F.trad := Id(id.lexema); }
   | num
     { F.trad := Num(num.valor); }
```

*Implementación directa en el parser mediante pasos y retornos de funciones.*

---

## 7. ETDS (Esquema de Traducción Dirigida por la Sintaxis)

El **ETDS** se implementa **en el parser** con las llamadas y retornos que simulan las reglas de traducción.

Ejemplo de implementación:
```python
def E(self):
    T_trad = self.T()
    E_p_trad = self.E_p(T_trad)
    return E_p_trad
```
➡ Corresponde a `{ E'.th := T.trad; E.trad := E'.trad }`

Y en:
```python
def E_p(self, th):
    if tok.clase == TKind.PLUS:
        T_trad = self.T()
        combinado = Bin('+', th, T_trad)
        return self.E_p(combinado)
```
➡ Cumple `{ E'₁.th := Bin('+', E'.th, T.trad); E'.trad := E'₁.trad }`

Cada paso del parser **ejecuta las acciones semánticas** que conforman el ETDS.

---

## 8. Ejemplo de Ejecución

<img width="503" height="388" alt="image" src="https://github.com/user-attachments/assets/5fc81374-3e37-4f2d-8865-7ea3538d7e2e" />

---

## 9. Conclusión

El programa implementa completamente un **ETDS funcional** para una **GIC aritmética**, incluyendo:
- Análisis léxico manual.  
- Parser recursivo LL(1).  
- Gramática de atributos heredados/sintetizados.  
- Generación del AST decorado y tabla de símbolos.  

Demuestra el proceso completo de traducción dirigida por la sintaxis desde la teoría hasta la implementación práctica
