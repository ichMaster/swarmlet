# Як працює evaluator виразів у Swarmlet

Якщо взяти інтерпретатор і обережно зняти з нього оболонку CLI, лексер, парсер, аналізатор і engine — все, що залишиться у середині, можна описати однією формулою:

```
evaluator : (AST, Context) -> Value
```

Це і є серце мови. Все інше — обгортки навколо цієї маленької функції. Лексер перетворює текст у токени, парсер — токени у дерево, аналізатор перевіряє це дерево на здоровий глузд, engine ганяє цю функцію по сітці клітинок. Але **обчислення сенсу виразу** — те, заради чого все будувалось — робиться в одному файлі: `swarmlet/eval.py`. І воно вміщується у ~100 рядків.

Цей документ — крок за кроком повз кожен `if isinstance` у `eval_expr`. Мета: показати, що інтерпретатор — це не магія, не "чорний ящик", а саме та функція, яку ви могли б написати самі за обідню перерву, якби хтось дав вам AST і сказав "ну добре, поверни значення".

Цей текст — найближчий аналог у нашій серії до [How does Prolog engine work](../../minilog/docs/prolog-engine-explained.md): такий самий механічний, "тицьмо пальцем у код, обходимо всі гілки, ось як це працює".

---

## Відкриваюча рамка: інтерпретатор — це функція

Давайте відразу скинемо містику. Слово "інтерпретатор" звучить серйозно — наче це окремий складний об'єкт, з менеджером пам'яті, з garbage collector-ом, з купою фаз. Для повноцінних мов це справді так. Але для **expression-евалюатора** Swarmlet'а ситуація куди простіша.

Подивіться на сигнатуру:

```python
def eval_expr(node: Any, ctx: ExprContext) -> Any:
    """Evaluate an expression AST node, returning a runtime value."""
```

Це функція. Вона приймає два аргументи — вузол AST і контекст — і повертає значення. Все. Більше ніяких прихованих змінних, ніяких побічних ефектів, ніяких глобальних станів. Один виклик `eval_expr(node, ctx)` повністю детермінований: для тих самих `node` і `ctx` він поверне той самий результат.

Це **дуже** важлива властивість. Вона означає, що ви можете тестувати evaluator у ізоляції — побудувати маленьке AST вручну, передати в нього синтетичний `ExprContext`, і перевірити вихідне значення. Жодних моків, жодного "піднімемо всю систему". Чиста функція приймає чисті аргументи і повертає чистий результат.

Друге, на що варто звернути увагу — як саме ця функція **дивиться** на свій аргумент. Вона не парсить рядок, не звертається до файлової системи, не питає в lexer-а нічого. Вона дивиться на **готовий AST-вузол** — тобто Python-об'єкт типу `A.Num`, `A.Var`, `A.BinOp` тощо — і вирішує, що з ним робити, на основі його **класу**:

```python
if isinstance(node, A.Num):
    return node.value
if isinstance(node, A.Bool):
    return node.value
if isinstance(node, A.Var):
    return _eval_var(node, ctx)
if isinstance(node, A.BinOp):
    return _eval_binop(node, ctx)
...
```

Це — **dispatch** по типу AST-вузла. У OCaml це робилося б через `match node with | Num n -> ... | Bool b -> ... | Var name -> ...`, де компілятор гарантує вичерпність. У Python ми мусимо писати ланцюжок `if isinstance`-ів, але семантично це те саме: один великий switch по конструктору.

І вся "магія інтерпретатора" зводиться до того, що деякі з цих гілок — наприклад, `A.BinOp` — рекурсивно викликають `eval_expr` для своїх піддерев. Тобто evaluator — це **fold по AST**: дерево обходиться знизу-вгору, листя (`Num`, `Bool`) повертають значення тривіально, а внутрішні вузли комбінують значення піддерев.

Якщо ви бачили хоч раз, як обчислюється арифметичний вираз через рекурсивний обхід дерева — ви вже знаєте, як працює evaluator Swarmlet. Решта — деталі.

---

## Контекст як незмінна торба

У Пролозі ми мали поняття **підстановки** (substitution) — словник, який ставить у відповідність змінним їхні значення. У Swarmlet'і аналог — це `ExprContext`. Подивимося на нього:

```python
@dataclass
class ExprContext:
    """Full evaluation context for expressions."""
    rng: np.random.Generator
    locals: Dict[str, Any] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    cell_states: set = field(default_factory=set)
    builtin_ctx: Optional[EvalContext] = None
    cell_xy: Optional[Tuple[int, int]] = None
    world: Any = None
    agent: Any = None
    is_init: bool = False
```

Це **торба з усім, що evaluator може потребувати**, щоб обчислити вираз. Тут є seeded RNG для випадковості (завдяки якому evaluator детермінований при фіксованому seed-і), словник `locals` із `let`-зв'язаних імен, словник `params` із декларованих параметрів моделі, множина імен станів клітинок, посилання на `world` (для builtins, які читають сітку), посилання на поточний `agent` (якщо ми всередині agent-rule), координати поточної клітинки `cell_xy`.

Ключова ідея: **контекст — immutable у логічному сенсі**. Коли evaluator натрапляє на `let x = 2 in body`, він не **мутує** `ctx.locals`, додаючи туди `x`. Він створює **новий** контекст із доданим зв'язуванням і передає його далі:

```python
if isinstance(node, A.Let):
    val = eval_expr(node.value, ctx)
    child_ctx = ctx.child(locals={node.name: val})
    return eval_expr(node.body, child_ctx)
```

Метод `child` робить копію словника `locals` (через `dict(self.locals)`) і додає туди нові зв'язування. Старий `ctx` залишається незайманим. Якщо `body` сам містить підвираз поза `let`-ом — він побачить **старий** контекст, без `x`. Це і є сенс лексичного скоупу: змінна доступна лише всередині свого `body`.

Паралель із minilog-овою підстановкою тут пряма. У Пролозі підстановка — це `Map[Var -> Term]`, і вона продовжується (extended) при кожній вдалій уніфікації. Ніколи не мутується — кожен крок створює нову. У Swarmlet'і `ctx.locals` — це `Map[str -> Value]`, і вона "продовжується" при кожному `let`-у через `ctx.child(...)`. Той самий шаблон: незмінні відображення, які копіюються-з-розширенням.

Чому це важливо? Бо це робить **backtracking безкоштовним**. Якщо evaluator пробує одну гілку `if`-а і вона повертає значення, ми переходимо до наступного коду з тим **самим** контекстом, що був до `if`-а. Ніяких "відкатів", ніяких "збережень/відновлень". У Пролозі це називається "trail" і потребує спеціальної структури даних. У нас — просто immutable дані.

---

## Прогулянка по `eval_expr`: один case за раз

Тепер пройдемо кожну гілку диспетчера. Я повторюватиму справжній код із `eval.py`, потім пояснюватиму, що відбувається.

### `Num` — числовий літерал

```python
if isinstance(node, A.Num):
    return node.value
```

Найпростіша гілка. Вузол AST `A.Num` має поле `.value` — Python-овий `float`. Ми просто повертаємо його. Жодних обчислень, жодної рекурсії — це **листя** дерева.

Якщо у програмі написано `3.14`, парсер перетворить це у `Num(value=3.14, line=...)`, і evaluator поверне `3.14`. Кінець історії.

### `Bool` — булевий літерал

```python
if isinstance(node, A.Bool):
    return node.value
```

Симетрично. `True` у вихідному коді стає `Bool(value=True)`, evaluator повертає Python-овий `True`. Знов листя.

### `Var` — посилання на змінну

```python
if isinstance(node, A.Var):
    return _eval_var(node, ctx)
```

Тут уже цікавіше. Літерали значень — це листя у тривіальному сенсі, але **змінна** — це посилання на щось у контексті. Evaluator делегує у `_eval_var`:

```python
def _eval_var(node: A.Var, ctx: ExprContext) -> Any:
    name = node.name
    if name in ctx.locals:
        return ctx.locals[name]
    if name in ctx.params:
        return ctx.params[name]
    if name in ctx.cell_states:
        return name  # state value
    result = _try_world_builtin(name, [], ctx, node.line)
    if result is not _SENTINEL:
        return result
    if name in BUILTINS:
        spec = BUILTINS[name]
        if spec.arity == 0:
            bctx = ctx.builtin_ctx or EvalContext(rng=ctx.rng)
            return spec.func(bctx)
    return name
```

Це впорядкований ланцюжок lookup-ів. Спочатку шукаємо у `locals` (let-зв'язування мають найвищий пріоритет — лексичний скоуп). Потім у `params` (параметри, оголошені на верхньому рівні моделі). Потім — а чи це часом не ім'я стану клітинки? Якщо `Tree` оголошено через `cell states Tree | Fire | Empty`, то `Var("Tree")` обчислюється у саме рядок `"Tree"` — це і є runtime-представлення стану. Потім — а чи це builtin без аргументів типу `state` чи `cell_state`, який залежить від поточної клітинки? Потім — глобальні 0-арні builtins типу `STAY`. І нарешті, як fallback — повертаємо саме ім'я як рядок (state-like), щоб не зривати виконання.

Цей пріоритет ідентичний пріоритету у будь-якій lexically-scoped мові: внутрішнє переважає зовнішнє. Якщо ви оголосили `param k = 5`, а потім написали `let k = 10 in k * 2`, то `k` всередині `let`-а — це 10 (з `locals`), а не 5 (з `params`).

### `BinOp` — бінарна операція

```python
if isinstance(node, A.BinOp):
    return _eval_binop(node, ctx)
```

Бінарна операція — це перший справжній **рекурсивний** випадок. Подивимось:

```python
def _eval_binop(node: A.BinOp, ctx: ExprContext) -> Any:
    op = node.op
    left = eval_expr(node.left, ctx)
    right = eval_expr(node.right, ctx)

    if op == "and":
        return _ensure_bool(left, node.line) and _ensure_bool(right, node.line)
    if op == "or":
        return _ensure_bool(left, node.line) or _ensure_bool(right, node.line)

    if op in ("==", "!="):
        if op == "==":
            return left == right
        return left != right

    if op in ("<", "<=", ">", ">="):
        l = _ensure_number(left, node.line, f" in '{op}'")
        r = _ensure_number(right, node.line, f" in '{op}'")
        if op == "<": return l < r
        if op == "<=": return l <= r
        if op == ">": return l > r
        return l >= r

    if op in ("+", "-", "*", "/", "mod"):
        l = _ensure_number(left, node.line)
        r = _ensure_number(right, node.line)
        if op == "+": return l + r
        if op == "-": return l - r
        if op == "*": return l * r
        if op == "/":
            if r == 0:
                raise SwarmletRuntimeError("division by zero", line=node.line)
            return l / r
        if op == "mod":
            return float(int(l) % int(r))
```

Тут я хочу, щоб ви помітили **порядок** операцій: `left = eval_expr(node.left, ctx)`, потім `right = eval_expr(node.right, ctx)`. Це і є **рекурсивний обхід дерева**. Якщо `node.left` сам — це `BinOp`, то `eval_expr` піде у нього, рекурсивно обчислить, поверне число — і ми продовжимо.

Зверніть увагу: ми обчислюємо `right` **завжди**, навіть для `and`/`or`. Це означає, що Swarmlet **не має short-circuit evaluation** для логічних операцій. У Python `False and X` не обчислює `X`. У нас обчислює. Це специфічний дизайн-вибір — для чистої функціональної мови без побічних ефектів він безпечний (зайва робота, але без сюрпризів). Якщо вам колись стане прикро від цього, перепишіть `_eval_binop` так, щоб для `and`/`or` обчислювати `right` ліниво — це буде ваше перше нетривіальне розширення.

Усі type-checks робляться через `_ensure_number` і `_ensure_bool`. Це runtime-перевірки: якщо ви написали `true + 1`, отримаєте `SwarmletRuntimeError("expected number but got bool")`. У статично типізованій мові ці помилки б ловив компілятор; у Swarmlet'і — runtime. Це осмислений компроміс для маленької educational мови.

### `UnOp` — унарна операція

```python
def _eval_unop(node: A.UnOp, ctx: ExprContext) -> Any:
    operand = eval_expr(node.operand, ctx)
    if node.op == "-":
        return -_ensure_number(operand, node.line)
    if node.op == "not":
        return not _ensure_bool(operand, node.line)
```

Найкоротший випадок з рекурсією. Один операнд, обчислюємо його, застосовуємо унарний оператор. Нічого нового.

### `Call` — виклик функції

```python
def _eval_call(node: A.Call, ctx: ExprContext) -> Any:
    name = node.func
    args = [eval_expr(a, ctx) for a in node.args]

    result = _try_world_builtin(name, args, ctx, node.line)
    if result is not _SENTINEL:
        return result

    if name in BUILTINS:
        spec = BUILTINS[name]
        bctx = ctx.builtin_ctx or EvalContext(rng=ctx.rng)
        return spec.func(bctx, *args)
    raise SwarmletRuntimeError(f"unknown function '{name}'", line=node.line)
```

Виклик функції у Swarmlet'і — це **завжди** виклик builtin. У мові немає user-defined функцій (це навмисно — модель cell/agent rules достатня, і це тримає інтерпретатор тривіальним). Тому тут лише два кроки:

1. Обчислити всі аргументи (left-to-right, eagerly): `args = [eval_expr(a, ctx) for a in node.args]`. Це знову рекурсія в evaluator.
2. Спробувати знайти функцію спочатку серед world-context builtins (через `_try_world_builtin`), потім серед глобальних builtins.

`_SENTINEL` — це маркерний об'єкт, який повертається, якщо `_try_world_builtin` не зміг обробити виклик (наприклад, бо `world` ще не доступний — ми у фазі init). Це Python-овий ідіом для "функція повертає Optional, але `None` — це валідне значення, тому потрібен окремий маркер".

### `Dot` — доступ до поля

```python
def _eval_dot(node: A.Dot, ctx: ExprContext) -> Any:
    obj = eval_expr(node.expr, ctx)
    if ctx.agent is not None and hasattr(ctx.agent, "fields"):
        if node.field_name in ctx.agent.fields:
            return ctx.agent.fields[node.field_name]
    if isinstance(obj, dict) and node.field_name in obj:
        return obj[node.field_name]
    if hasattr(obj, node.field_name):
        return getattr(obj, node.field_name)
    raise SwarmletRuntimeError(
        f"cannot access field '{node.field_name}'", line=node.line
    )
```

`Dot` — це доступ до поля об'єкта: `self.heading`, `agent.energy`. Спочатку обчислюємо ліву частину (`node.expr` — наприклад, `self`), потім шукаємо поле трьома способами: у `agent.fields` (бо у Swarmlet-агента поля живуть у словнику `fields`), у dict-об'єкті, або через Python-овий `getattr`. Це pragmatic-fallback, типовий для динамічних мов.

### `If` — умовний вираз

```python
if isinstance(node, A.If):
    cond = eval_expr(node.cond, ctx)
    cond_val = _ensure_bool(cond, node.line)
    if cond_val:
        return eval_expr(node.then_expr, ctx)
    return eval_expr(node.else_expr, ctx)
```

Ось тут **і є** короткозамкнуте обчислення. Ми обчислюємо умову, потім — **лише одну з двох гілок**. Це ключова відмінність від `BinOp`-а, де обчислюються обидва операнди. У `If`-а ми обчислюємо рівно одне з двох піддерев — те, що відповідає істинному значенню `cond`.

`If` у Swarmlet'і — це **вираз**, а не statement. Тобто він повертає значення, і обидві гілки мусять повертати значення сумісного типу. Якщо ви напишете `if x > 0 then 1 else true`, аналізатор має це впіймати — а evaluator просто поверне різні типи для різних гілок без скарг (в дусі динамічної мови).

### `Let` — локальне зв'язування

```python
if isinstance(node, A.Let):
    val = eval_expr(node.value, ctx)
    child_ctx = ctx.child(locals={node.name: val})
    return eval_expr(node.body, child_ctx)
```

Це той випадок, який ми вже бачили вище. Покроково:

1. Обчислюємо `value` у поточному контексті. Важливо, що ми обчислюємо ДО створення child-context-а — тобто `value` НЕ бачить нову зв'язку. Це робить `let x = x + 1 in ...` обчисленням з зовнішнім `x` справа і новим `x` всередині `body`. Це **non-recursive let** — що нормально для звичайних let-виразів.
2. Створюємо child-context із доданим `{name: val}`.
3. Обчислюємо `body` у новому контексті.

`let x = 2 in x * 3` -> обчислюємо `2`, кладемо `x = 2.0` у child-context, обчислюємо `x * 3` у цьому контексті: `_eval_var` знаходить `x` у `locals`, повертає `2.0`, потім `BinOp(*)` дає `6.0`.

### `Match` — pattern matching

```python
if isinstance(node, A.Match):
    return _eval_match(node, ctx)
```

```python
def _eval_match(node: A.Match, ctx: ExprContext) -> Any:
    subject = eval_expr(node.subject, ctx)
    for case in node.cases:
        if _match_case(case, subject, ctx):
            return eval_expr(case.body, ctx)
    raise SwarmletRuntimeError("non-exhaustive match", line=node.line)
```

Обчислюємо `subject`, проходимо по `cases` зверху вниз, для кожного питаємо `_match_case`, чи він пасує. Перший, що пасує — обчислюємо його `body` і повертаємо. Жоден не пасує — runtime error.

`_match_case` перевіряє, чи **хоч один** з `or-patterns` випадку пасує до subject, і додатково — чи проходить guard:

```python
def _match_case(case: A.MatchCase, subject: Any, ctx: ExprContext) -> bool:
    matched = any(_match_pattern(p, subject) for p in case.patterns)
    if not matched:
        return False
    if case.guard is not None:
        guard_val = eval_expr(case.guard, ctx)
        return _ensure_bool(guard_val, case.line)
    return True
```

`_match_pattern` робить власне порівняння: wildcard завжди пасує, identifier пасує до stringу-стану, number/bool — до literal-значення. Деталі — у [pattern-matching-explained.md](pattern-matching-explained.md), тут нам важливо лише, що evaluator *використовує* цю функцію як предикат.

---

## Повний trace одного обчислення

Давайте проженемо `let x = 2 in x * 3` через evaluator, фіксуючи стан контексту на кожному кроці.

**Старт.** AST виглядає так (умовно):

```python
Let(
    name="x",
    value=Num(2.0),
    body=BinOp("*", Var("x"), Num(3.0))
)
```

Контекст `ctx_0`:
```
ctx_0 = ExprContext(rng=R, locals={}, params={}, cell_states={...}, ...)
```

**Крок 1.** `eval_expr(Let(...), ctx_0)`. Диспетчер бачить `isinstance(node, A.Let)`, заходить у відповідну гілку.

**Крок 2.** `val = eval_expr(Num(2.0), ctx_0)`. Диспетчер бачить `isinstance(node, A.Num)`, повертає `2.0`. `val = 2.0`.

**Крок 3.** `child_ctx = ctx_0.child(locals={"x": 2.0})`. Створюємо `ctx_1`:
```
ctx_1 = ExprContext(rng=R, locals={"x": 2.0}, params={}, ...)
```
Зверніть увагу: `ctx_0.locals` досі `{}`. Незмінні дані.

**Крок 4.** `eval_expr(BinOp("*", Var("x"), Num(3.0)), ctx_1)`. Диспетчер бачить `BinOp`, делегує у `_eval_binop`.

**Крок 5.** `left = eval_expr(Var("x"), ctx_1)`. Диспетчер бачить `Var`, делегує у `_eval_var`. Той дивиться у `ctx_1.locals`, знаходить `"x" -> 2.0`, повертає `2.0`. `left = 2.0`.

**Крок 6.** `right = eval_expr(Num(3.0), ctx_1)`. Літерал, повертає `3.0`. `right = 3.0`.

**Крок 7.** Оператор `*`, `_ensure_number(2.0)` -> `2.0`, `_ensure_number(3.0)` -> `3.0`, повертаємо `2.0 * 3.0 = 6.0`.

**Крок 8.** `_eval_binop` повертає `6.0`. `eval_expr` для `BinOp` повертає `6.0`. `eval_expr` для `Let` повертає `6.0`.

**Кінець.** Результат: `6.0`. Контекст `ctx_0` досі цілий і незмінний — child-context `ctx_1` помер як локальна змінна, garbage collector прибере.

Якщо ви візьмете будь-який Swarmlet вираз і пройдете його так само — рекурсивно, з фіксацією контексту на кожному кроці — ви повністю зрозумієте, як працює evaluator. Більше нічого там немає.

---

## OCaml-міст: той самий evaluator з реальними ADT

У Python ми мусимо писати ланцюжок `isinstance`-ів, бо AST-вузли — це окремі класи, і Python не має sum-types на рівні мови. У OCaml те саме виражається набагато компактніше — і компілятор гарантує, що ви не забули жодного випадку.

```ocaml
(* AST: один тип з кількома конструкторами — це ADT *)
type expr =
  | Num of float
  | Bool of bool
  | Var of string
  | BinOp of string * expr * expr
  | If of expr * expr * expr
  | Let of string * expr * expr
  | Match of expr * (pattern * expr option * expr) list

and pattern =
  | PWild
  | PIdent of string
  | PNum of float
  | PBool of bool

(* Значення runtime — теж sum-type *)
type value =
  | VNum of float
  | VBool of bool
  | VState of string

(* Контекст — immutable map *)
module Ctx = Map.Make(String)
type ctx = value Ctx.t

(* Evaluator: pattern match на AST вузлі *)
let rec eval_expr (node : expr) (ctx : ctx) : value =
  match node with
  | Num n -> VNum n
  | Bool b -> VBool b
  | Var name ->
      (try Ctx.find name ctx
       with Not_found -> VState name)
  | BinOp (op, l, r) ->
      let lv = eval_expr l ctx in
      let rv = eval_expr r ctx in
      eval_binop op lv rv
  | If (cond, then_e, else_e) ->
      (match eval_expr cond ctx with
       | VBool true -> eval_expr then_e ctx
       | VBool false -> eval_expr else_e ctx
       | _ -> failwith "if condition must be bool")
  | Let (name, value_e, body_e) ->
      let v = eval_expr value_e ctx in
      let ctx' = Ctx.add name v ctx in
      eval_expr body_e ctx'
  | Match (subject, cases) ->
      let s = eval_expr subject ctx in
      eval_match s cases ctx

and eval_binop op lv rv =
  match op, lv, rv with
  | "+", VNum a, VNum b -> VNum (a +. b)
  | "*", VNum a, VNum b -> VNum (a *. b)
  | "and", VBool a, VBool b -> VBool (a && b)
  (* ... *)
  | _ -> failwith "type error"

and eval_match s cases ctx =
  match cases with
  | [] -> failwith "non-exhaustive match"
  | (pat, guard, body) :: rest ->
      if pattern_matches pat s
         && (match guard with
             | None -> true
             | Some g -> eval_expr g ctx = VBool true)
      then eval_expr body ctx
      else eval_match s rest ctx

and pattern_matches pat s =
  match pat, s with
  | PWild, _ -> true
  | PIdent name, VState s -> name = s
  | PNum n, VNum m -> n = m
  | PBool b, VBool c -> b = c
  | _ -> false
```

Те саме, що ми маємо в Python, але:

1. **Sum-types — частина мови.** `type expr = Num of ... | Bool of ... | ...` — це і є наш AST, без окремих класів і без `isinstance`.
2. **`match` exhaustivity.** Якщо ви додасте новий конструктор `Lambda` у `expr` і забудете обробити його у `eval_expr`, OCaml-компілятор скаже: "warning: this pattern-matching is not exhaustive: Lambda not matched". У Python такої гарантії немає.
3. **Контекст як `Map`.** OCaml має stdlib-овий `Map.Make`, що дає immutable-by-default map. Метод `Ctx.add` повертає новий map, не мутуючи старий — точно як `ctx.child(locals=...)` у Python.
4. **Один великий `match` замість ланцюжка `if`-ів.** Семантично однаково, але візуально набагато чистіше — і компілятор має повну картину для перевірок.

Якщо ви прочитаєте `eval_expr` у нашому Python-коді і `eval_expr` тут у OCaml — це **той самий алгоритм**. Просто Python змушує писати його в "ручному" стилі, а OCaml дає синтаксис, який ідеально підходить під цю задачу. Це і є причина, чому компілятори і інтерпретатори традиційно пишуться у мовах ML-родини.

---

## Python vs OCaml: isinstance dispatch vs ADT

Кілька конкретних точок порівняння, які варто тримати в голові.

**Розширюваність vs безпечність.** У Python додати новий тип AST-вузла легко: створіть новий клас, додайте `if isinstance(node, NewType): ...` у `eval_expr`. Якщо забудете додати — отримаєте `SwarmletRuntimeError("unknown expression node: NewType")` у runtime. У OCaml додати новий конструктор означає, що компілятор негайно покаже всі місця, де ви забули його обробити — на стадії компіляції, не runtime. Це fundamental-trade-off між динамічністю і статичною безпекою.

**Performance.** `isinstance`-перевірки — це O(1) у Python, але кожна — це окремий виклик типу-перевірки. У OCaml `match`-вираз компілюється у `switch` на тегах конструкторів, що ще швидше. Для educational-інтерпретатора це не має значення; для production — має.

**Шум коду.** Python `eval_expr` — це ~40 рядків з ланцюжком if-ів, плюс кілька допоміжних функцій. OCaml — це ~25 рядків одного `match`-виразу. Ця різниця масштабується дуже швидко: AST з 50 типами вузлів у Python — це жахливий ланцюжок if-ів; у OCaml — досі один `match` на 50 кейсів, який легко читається.

**Type-safety values.** У Python наші runtime-значення — це просто `Any` (Python-овий float, bool, str, None). Тип-теги ми перевіряємо вручну через `_type_tag` і `_ensure_number`. У OCaml ми б мали `type value = VNum of float | VBool of bool | VState of string`, і компілятор не дав би нам сплутати їх. Більше коду на boilerplate (треба явно загортати/розгортати), але нуль runtime-помилок типу "expected number but got bool".

---

## Поширені граблі

### 1. Контекст не immutable у глибокому сенсі

`ctx.child(locals=...)` робить **shallow copy** словника `locals`. Якщо значення у словнику — це список або dict, і ви якось мутуєте його глобально, мутація буде видна у обох контекстах. У Swarmlet'і це не проблема, бо runtime-значення — це примітиви (float, bool, str), які immutable за визначенням. Але якщо ви будете розширювати мову і додавати, скажімо, list-значення — пам'ятайте про це. Один реальний баг такого роду — це коли у `params` лежить mutable dict, і одне правило випадково мутує його; інше правило бачить нову версію.

### 2. Eager evaluation у `BinOp` для `and`/`or`

Як я вже згадував, наш evaluator обчислює обидва операнди `and`/`or` завжди. Це означає, що написати `let safe = x != 0 and (1.0 / x) > 0.5` — небезпечно: ділення на нуль виконається навіть якщо `x == 0`, і ви отримаєте runtime error. У Python такий код безпечний, бо `and` short-circuit. У Swarmlet'і — ні. Це не баг evaluator-а, це його дизайн-вибір; але про нього легко забути.

### 3. Var fallback на ім'я як рядок

Останній рядок `_eval_var`: `return name`. Тобто якщо ім'я не знайдено ніде — у `locals`, `params`, `cell_states`, builtins — evaluator повертає **сам рядок-ім'я** як значення. Це pragmatic fallback для випадку "це невідоме state-ім'я, але аналізатор пропустив його — давайте не зриватись". На практиці це може маскувати typo: якщо ви напишете `Trre` замість `Tree`, evaluator поверне рядок `"Trre"`, який потім порівняється з `"Tree"` у match-арці і не пасуватиме — ви побачите неочікувану поведінку без зрозумілої помилки. У строгій версії evaluator-а ви б замінили цей fallback на `raise SwarmletRuntimeError("undefined name")`. Аналізатор має ловити такі речі заздалегідь, але fallback тут — підстраховка, що часом грає проти вас.

---

## Вправи

### Вправа 1: trace evaluator-а на `if`-каскаді

**Setup.** Візьміть Swarmlet-вираз:

```swl
let energy = 5 in
if energy > 10 then 1.0
else if energy > 0 then 0.5
else 0.0
```

**Task.** Покроково пройдіть `eval_expr` для нього, фіксуючи `ctx.locals` на кожному кроці. Скільки разів викликається `eval_expr`? Які гілки `If` обчислюються, а які — ні?

**Hint.** Пам'ятайте, що `If` — короткозамкнутий: обчислюється лише та гілка, що відповідає істинному значенню `cond`. Тут `cond` — це `BinOp(">", Var("energy"), Num(10.0))`, що обчислюється у `False`. Тому evaluator іде у `else_expr`, який сам — це інший `If`. І так далі.

### Вправа 2: додайте short-circuit для `and`/`or`

**Setup.** Зараз `_eval_binop` обчислює `right` для `and`/`or` беззастережно.

**Task.** Перепишіть `_eval_binop` так, щоб для `and` `right` обчислювався лише якщо `left` — `True`, а для `or` — лише якщо `left` — `False`. Додайте unit-test, що показує `let x = 0 in x != 0 and (1.0 / x) > 0.5` тепер не зриває division by zero.

**Hint.** Подивіться, як обробляється `If` — там `eval_expr(then_expr, ctx)` чи `eval_expr(else_expr, ctx)` викликається лише для однієї гілки. Зробіть те саме для `and`/`or`: спочатку обчисліть `left`, потім вже за умовою — `right`.

### Вправа 3: додайте новий тип AST-вузла

**Setup.** Уявіть, що ви хочете додати triplet-conditional `cond ?? then_e :: else_e :: third_e`, який бере перше істинне з двох умов і повертає відповідне значення (а якщо обидві хибні — третє).

**Task.** Додайте новий dataclass `A.Cond3(cond1, then1, cond2, then2, default)` у `ast.py`. Додайте відповідну гілку у `eval_expr`. Як ця гілка має виглядати, щоб залишатись короткозамкнутою?

**Hint.** Структурно це майже як `If`, тільки з двома послідовними перевірками. Спочатку `eval_expr(node.cond1, ctx)`, якщо `True` — `eval_expr(node.then1, ctx)`, інакше `eval_expr(node.cond2, ctx)`, і так далі. Парсер чіпати не треба — для вправи побудуйте AST вручну і тестуйте безпосередньо `eval_expr`.

### Вправа 4: переписати evaluator на одному `match`-виразі (Python 3.10+)

**Setup.** Python 3.10 додав `match`-statement з підтримкою class patterns. Ви можете писати:

```python
match node:
    case A.Num(value=v):
        return v
    case A.Bool(value=b):
        return b
    case A.Var(name=n):
        return _eval_var(node, ctx)
    ...
```

**Task.** Перепишіть `eval_expr` із `if isinstance` ланцюжка у Python `match`. Порахуйте різницю у кількості рядків. Чи з'явились якісь warning-и від лінтера про non-exhaustive match?

**Hint.** Python `match` — це pattern matching на рівні runtime, не compile-time. Він не дає вам статичної гарантії exhaustivity (на відміну від OCaml). Але візуально код стає набагато чистішим, і це найближче, що Python може дати до OCaml-стилю. Подивіться на [pattern-matching-explained.md](pattern-matching-explained.md) для глибшого порівняння.

---

## Підсумок

Evaluator виразів у Swarmlet'і — це функція з двома аргументами і одним поверненим значенням. Все, що вона робить — це **диспетчер по типу AST-вузла**, з рекурсивними викликами для піддерев і незмінним контекстом, що передається крізь рекурсію. Жодного hidden state, жодного mutability, жодних побічних ефектів (крім помилок).

Це той самий шаблон, що ви побачите у будь-якій книжці по інтерпретаторах функціональних мов — від маленького "схема-у-схемі" Sussmann-а до дорослих ML-компіляторів. Різниця тільки у тому, скільки типів AST-вузлів, скільки runtime-значень, і яка експресивність контексту. Серце — однакове.

Якщо ви зрозуміли цей документ, ви розумієте, як працює Swarmlet — на 80%. Решта — це лексер (текст -> токени), парсер (токени -> AST), аналізатор (AST -> AST з помилками), engine (повторне застосування evaluator-а до сітки клітинок). Все це обертається навколо `eval_expr`. Це і є справжній центр.

---

## Read together

- [SPEC.md](../specification/Swarmlet-SPEC.md) — повна семантика мови
- [algebraic-data-types.md](algebraic-data-types.md) — Tier 3 sibling: чому AST і runtime values природньо моделюються як ADT
- [pattern-matching-explained.md](pattern-matching-explained.md) — Tier 1: глибше на тему pattern matching, який ми тут тільки оглядово зачепили
