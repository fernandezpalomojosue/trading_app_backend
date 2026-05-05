Sí—intentar meter todo “Execution Plans” de golpe es una receta para romper producción 😄. Esto hay que **trocearlo en iteraciones pequeñas, cada una deployable y reversible**.

Te propongo un plan por **fases incrementales**, donde cada paso aporta valor sin bloquear lo siguiente:

---

## 🧩 Fase 0 — Estabilizar lo actual (muy importante)

Antes de añadir nada:

* Corrige duplicación del cron (lo de `Signal worker started` repetido)
* Añade **idempotencia básica**:

  * unique constraint: `(stock, strategy_id, timestamp_bucket)`
* Añade logs estructurados (request_id / job_id)

👉 Objetivo: que el sistema actual sea **predecible**

---

## 🧩 Fase 1 — Separar “qué evaluar” del cron

Ahora mismo el cron decide TODO.

Cambia eso:

### Nuevo concepto interno (sin exponer aún):

```python
class EvaluationTarget:
    strategy_id: UUID
    stocks: list[str]
```

Y creas un servicio:

```python
class EvaluationTargetService:
    async def get_targets() -> list[EvaluationTarget]:
        ...
```

### Implementación inicial (simple):

* Por ahora:

  * 1 estrategia (default)
  * stocks = favoritos o fallback

👉 El cron ahora hace:

```python
targets = await evaluation_target_service.get_targets()

for target in targets:
    for stock in target.stocks:
        run(strategy, stock)
```

💥 Ya desacoplaste el sistema sin romper nada.

---

## 🧩 Fase 2 — Introducir ExecutionPlan (mínimo viable)

Ahora sí, DB:

### Tabla simple (NO te compliques aún):

```sql
execution_plans
- id
- user_id
- strategy_id
- stocks JSONB
- timeframe
- is_active
```

👉 Nada de cron por plan todavía.

### Cambias SOLO esto:

```python
get_targets():
    plans = SELECT * WHERE is_active = true
    
    return [
        EvaluationTarget(
            strategy_id=plan.strategy_id,
            stocks=plan.stocks
        )
    ]
```

👉 Ya tienes:

* múltiples estrategias
* múltiples combinaciones
* sistema agnóstico al usuario

💥 Sin tocar el scheduler

---

## 🧩 Fase 3 — Evitar duplicados (clave)

Ahora aparece el problema real:
múltiples planes pueden evaluar lo mismo.

### Solución simple:

Antes de generar señal:

```python
cache_key = f"signal:{strategy_id}:{stock}:{time_bucket}"

SET key NX EX 60
```

Si falla → skip

👉 Esto usa tu Redis actual (solo añade `nx=True`)

💥 Idempotencia sin rediseñar DB

---

## 🧩 Fase 4 — Optimización real (aquí empieza lo interesante)

Ahora sí mejoras rendimiento:

### 1. Agrupar por stock

En vez de:

```
plan1 -> AAPL
plan2 -> AAPL
```

Haz:

```python
stock_map = {
    "AAPL": [strategy1, strategy2],
    "TSLA": [strategy1]
}
```

Y fetch market data **una sola vez**

---

### 2. Cachear indicadores

Ya tienes Redis → úsalo:

```python
key = f"indicators:{stock}:{timeframe}:{date}"
```

💥 esto reduce brutalmente el costo

---

## 🧩 Fase 5 — Scheduling real (opcional, después)

Aquí decides si complicarte o no.

### Opción simple (recomendada):

* Un solo cron global (cada X minutos)
* Todos los planes se evalúan

### Opción avanzada:

Añadir:

```sql
next_run_at TIMESTAMP
```

Y filtrar:

```sql
WHERE next_run_at <= now()
```

💥 Solo lo haces cuando escale de verdad

---

## 🧩 Fase 6 — API (recién aquí)

Endpoints:

* POST /execution-plans
* GET /execution-plans
* PATCH /execution-plans/{id}
* DELETE /execution-plans/{id}

👉 No antes. Evita diseñar APIs para algo que aún no corre bien.

---

## ⚠️ Lo importante (donde te equivocabas un poco)

Tu idea original:

> “precomputar qué stocks evalúa cada estrategia”

Eso **está bien**, pero:

❌ hacerlo estático es mala idea
✅ hacerlo dinámico vía `ExecutionPlan` es correcto

---

## 🧠 Regla clave

> Primero desacopla → luego modela → luego optimiza → luego escala

No al revés.

---

## 🚀 Si quieres subir el nivel

En el siguiente paso puedo ayudarte a:

* Diseñar el `EvaluationTargetService` limpio
* Añadir `nx=True` correctamente a tu RedisCache
* Reescribir tu `run_signal_job()` sin duplicaciones
* O convertir esto en un mini sistema tipo “Airflow-lite”

Solo dime por cuál fase quieres empezar 👍
