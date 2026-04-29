# 📘 Trading Strategy DSL — Design Specification v1

## 1. 🎯 Objetivo

Diseñar un sistema de estrategias de trading basado en un DSL (Domain Specific Language) representado en JSON, que permita:

- Definir estrategias de forma flexible y extensible
- Evaluar condiciones sobre datos de mercado en tiempo real o backtesting
- Integrar generación asistida por IA
- Evitar hardcoding de lógica de trading

---

## 2. 🧠 Concepto central

Una estrategia es una expresión lógica evaluable (AST) compuesta por:

- Nodos lógicos (`AND`, `OR`, `NOT`)
- Condiciones (comparaciones entre expresiones)

---

## 3. 🌳 Estructura general

```json
{
  "type": "AND" | "OR" | "NOT" | "condition"
}
```

---

## 4. 🔗 Nodos lógicos

### 4.1 AND / OR

```json
{
  "type": "AND",
  "children": [ Expression, Expression ]
}
```

```json
{
  "type": "OR",
  "children": [ Expression, Expression ]
}
```

---

### 4.2 NOT

```json
{
  "type": "NOT",
  "child": Expression
}
```

---

## 5. ⚙️ Condiciones

### 5.1 Definición

Una condición es una operación entre dos expresiones que retorna un booleano.

```json
{
  "type": "condition",
  "left": Expression,
  "operator": "string",
  "right": Expression
}
```

---

### 5.2 Operadores soportados

#### Comparación
- `<`
- `<=`
- `>`
- `>=`
- `==`
- `!=`

#### Eventos
- `cross_above`
- `cross_below`

---

## 6. 📦 Expresiones

Una expresión es cualquier elemento evaluable a un valor.

---

### 6.1 Constant

```json
{
  "type": "constant",
  "value": 30
}
```

---

### 6.2 Price

```json
{
  "type": "price",
  "field": "open" | "high" | "low" | "close" | "volume"
}
```

---

### 6.3 Indicator

```json
{
  "type": "indicator",
  "name": "RSI" | "SMA" | "EMA",
  "params": {
    "period": 14
  }
}
```

---

## 7. 🔄 Evaluación (Execution Model)

Evaluación recursiva del AST:

- AND → todos true
- OR → alguno true
- NOT → negación del child
- condition → evaluación de left y right + operador

---

## 8. ⚡ Engine conceptual

```python
def evaluate(node, context):
    if node["type"] == "AND":
        return all(evaluate(c, context) for c in node["children"])

    if node["type"] == "OR":
        return any(evaluate(c, context) for c in node["children"])

    if node["type"] == "NOT":
        return not evaluate(node["child"], context)

    if node["type"] == "condition":
        left = eval_expr(node["left"], context)
        right = eval_expr(node["right"], context)
        return apply_operator(node["operator"], left, right)
```

---

## 9. 📊 Contexto de evaluación

El engine depende de un contexto de mercado:

- OHLCV data
- indicadores calculados o dinámicos
- timestamp actual

---

## 10. 🧠 Integración con IA

La IA no interactúa directamente con el engine.

### Flujo recomendado

Usuario → IA → JSON DSL → Validator → Engine

Opcional:

Usuario → IA (refine intent) → IA (generate DSL) → Validator → Engine

---

## 11. 🛡️ Validación

Antes de ejecución:

- Validación de schema JSON
- Operadores válidos
- Indicadores registrados
- Estructura correcta del AST

---

## 12. 📈 Extensibilidad

El sistema permite extender sin modificar el core:

- Añadir indicadores vía registry
- Añadir operadores vía registry
- Añadir nuevos tipos de expresión

---

## 13. ⚠️ Decisiones de diseño clave

- NOT es un nodo lógico explícito
- No hay parsing de lenguaje natural en el core
- DSL completamente estructurado en JSON
- Evaluación recursiva pura
- IA como generador de estructura, no ejecutor

---

## 14. 🚀 Resultado esperado

Este diseño permite:

- Estrategias complejas arbitrarias
- Backtesting consistente
- Ejecución en tiempo real
- Generación asistida por IA
- Extensión sin romper el core

