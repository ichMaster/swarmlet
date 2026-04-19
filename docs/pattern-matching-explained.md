# Як працює pattern matching у Swarmlet

Pattern matching — це одна з тих речей, які виглядають як "ну це просто `switch`-statement з кращим синтаксисом", і саме через це сприйняття його сила ніколи до кінця не доходить до людей з імперативного бекграунду. Цей документ — спроба показати, що pattern matching насправді робить **три різні речі одночасно** в одному синтаксичному конструкторі, і чому ця комбінація фундаментально змінює стиль того, як ви пишете код.

Рухатимемось знизу вгору: подивимося на конкретний `match` із `forest_fire.swl`, розберемо його як AST, порівняємо з Python (старим і Python 3.10) і зрештою зробимо місток до OCaml. Мета — дати не просто "розумію як це парситься", а "розумію, **чому** мова з pattern matching пишеться інакше".

Технічна довідка по семантиці — у [SPEC.md секція 7.4](../specification/Swarmlet-SPEC.md#74-pattern-matching-semantics). Цей документ не дублює спеку, а пояснює, **навіщо** правила саме такі.

---

## Відкриваюча рамка: три ролі в одному конструкторі

Якщо запитати у Java- чи Python-програміста (без досвіду з Python 3.10+ `match`), що таке pattern matching, найчастіша відповідь буде "це красивий `switch`". Це правда лише на одну третину.

Pattern matching робить **три речі одразу**:

1. **Discrimination** — розрізнення варіантів. "Це `Tree` чи `Fire` чи `Empty`?" Це те, що `switch` теж робить.
2. **Destructuring** — розкладання структурованого значення на компоненти. "Якщо це пара `(x, y)`, дай мені `x` і `y` окремо." Цього у `switch` нема.
3. **Binding** — прив'язка частин до імен у новому скоупі. "Якщо тут число, назви його `n` і використай у тілі гілки." Цього у `switch` теж нема.

У Swarmlet v0.1 третя роль навмисно **відключена** — змінних-в-патерні немає. Але важливо одразу зрозуміти повну картину, бо це пояснює, чому OCaml-програміст пише функції майже без `if`-ів, а імперативний програміст не може второпати, як таке взагалі можливо.

Ще одна річ, яку треба сказати на старті: pattern matching у функціональних мовах — це **вираз**, а не **statement**. Він повертає значення:

```swl
let result = match state with
  | Tree -> 1
  | Fire -> 2
  | _    -> 0
in
  result + 10
```

У імперативному `switch` ви б писали `int result; switch (...) { case ...: result = 1; break; ... }` — три рядки шуму навколо одного рішення. Ця різниця "вираз vs statement" не косметична, вона радикально впливає на щільність коду — у типовій Swarmlet-програмі ви не побачите мутабельних змінних, бо `match` разом із `let ... in ...` і тернарним `if` дають усе потрібне для обчислення значень без присвоювань.

---

## Базова механіка: як движок Swarmlet виконує `match`

Давайте подивимося на простий приклад, який міг би жити у `forest_fire.swl` (хоч поточна версія написана через `if`-каскади — ми покажемо нижче, чому):

```swl
let cell Tree =
  match any Fire with
  | true  -> Fire
  | false -> Tree
```

Що тут відбувається при кожному обчисленні правила для клітинки у стані `Tree`?

1. Інтерпретатор бере вираз-**suject** (об'єкт розгляду) — `any Fire`. Це builtin, який повертає `bool`: чи є хоч одна сусідня клітинка у стані `Fire`.
2. Получене значення (скажімо, `true`) порівнюється послідовно з кожним патерном зверху вниз.
3. Перший патерн — `true`. Збігається. Тіло гілки — `Fire`. Це і буде новим станом клітинки.

Коли inferred-значення `false`, перша гілка не збігається, рухаємося до другої — `false` збігається, повертається `Tree`.

### AST walkthrough

Парсер перетворює цей фрагмент у дерево вузлів. Подивімося на форму (читайте `swarmlet/ast.py` для повного визначення):

```
Match(
  subject = Call(func='any', args=[Var('Fire')]),
  cases = [
    MatchCase(
      patterns = [Pattern(kind='bool', value=True)],
      guard = None,
      body = Var('Fire'),
    ),
    MatchCase(
      patterns = [Pattern(kind='bool', value=False)],
      guard = None,
      body = Var('Tree'),
    ),
  ],
)
```

Ключові спостереження:

- **`subject` — це довільний вираз**. Не лише змінна. Може бути виклик функції, арифметика, інший `match` (у дужках) — будь-що, що обчислюється у значення.
- **`cases` — список**. Порядок важливий. Перший збіг виграє.
- **`patterns` всередині `MatchCase` — теж список**. Це or-патерни: гілка спрацьовує, якщо **будь-який** з патернів збігся.
- **`guard` — необов'язковий вираз `bool`**. Якщо він є, гілка спрацьовує, лише коли і патерн збігся, **і** guard повертає `true`.
- **Жодних bindings**. У версії v0.1 патерн ніколи не вводить нових імен у скоуп. Це навмисне обмеження, ми пояснимо чому.

### Як це інтерпретує `_eval_match`

У `swarmlet/eval.py` інтерпретація гранично проста:

```python
def _eval_match(node, ctx):
    subject = eval_expr(node.subject, ctx)
    for case in node.cases:
        if _match_case(case, subject, ctx):
            return eval_expr(case.body, ctx)
    raise SwarmletRuntimeError("non-exhaustive match", line=node.line)

def _match_case(case, subject, ctx):
    matched = any(_match_pattern(p, subject) for p in case.patterns)
    if not matched:
        return False
    if case.guard is not None:
        guard_val = eval_expr(case.guard, ctx)
        return _ensure_bool(guard_val, case.line)
    return True
```

Обчисли subject, пройдись по кейсах зверху вниз, перевір чи якийсь or-патерн збігся, якщо є guard — обчисли і його, поверни тіло першої успішної гілки. Інакше — `SwarmletRuntimeError("non-exhaustive match")`. Це наївна реалізація; у продакшн-компіляторах (OCaml) match-вирази оптимізуються в decision trees, але для Swarmlet з 3-5 патернами на гілку лінійний скан — не вузьке місце.

---

## Чотири види патернів у v0.1

Спека (секція 7.4) визначає чотири види патернів. Розберемо кожен.

### 1. Wildcard `_`

Збігається з будь-чим. Універсальний catch-all. Завжди останній у списку гілок, бо інакше "затіняє" наступні (вони ніколи не виконаються).

```swl
match state with
| Tree -> Fire
| _    -> state    # все інше залишається без змін
```

Без `_` (або без вичерпання всіх можливих значень) ризикуєте отримати runtime error "non-exhaustive match".

### 2. Літеральні числа

Збігаються за рівністю. Працюють як з цілими, так і з float.

```swl
match self.energy with
| 0   -> die
| 1   -> stay
| _   -> move (random_dir ())
```

Гілки `0` і `1` спрацьовують при точній рівності. Тонкість: у Swarmlet усі числа — `float` (див. `_ensure_number`), тому патерн `0` збігається з `0.0`. `_match_pattern` явно виключає `bool` зі збігу за числовим патерном, бо в Python `True == 1` повертає `True`, а нам цього не треба.

### 3. `true` / `false`

Збігаються з відповідним booleanом.

```swl
match any Fire with
| true  -> Fire
| false -> Tree
```

Чек `isinstance(subject, bool)` тут навмисний — `1 == true` для патерн-метчингу має повертати `false`.

### 4. Ідентифікатор у позиції патерна — це **state name**

Це найважливіше і найнеочікуваніше для людей з OCaml/Rust-бекграундом правило. У Swarmlet v0.1 ідентифікатор у позиції патерна **завжди** інтерпретується як ім'я cell-state, ніколи як binding.

```swl
cell states Empty | Tree | Fire | Ash

let cell c =
  match state with
  | Empty -> Tree         # збіг якщо state == "Empty"
  | Tree  -> Fire         # збіг якщо state == "Tree"
  | Fire  -> Ash          # збіг якщо state == "Fire"
  | Ash   -> Empty        # збіг якщо state == "Ash"
```

Тобто `Empty` тут — це **літерал**, не змінна. Якби ви написали в OCaml `match s with | x -> ...`, `x` був би binding-ом і завжди збігався б з будь-чим. У Swarmlet `Empty` (з великої літери чи з маленької — байдуже, синтаксично) — це завжди порівняння з відомою константою.

**Чому таке обмеження?** Спека прямо пояснює: "це робить патерни однозначними без статичного типового pass-у". У OCaml компілятор знає, що `Some x` — конструктор з аргументом, а `x` сам по собі — binding, бо є повна типова інформація. У Swarmlet — динамічно-типізований runtime з 6 тегами (`number`, `bool`, `state`, `direction`, `agent_type`, `void`) без user-defined ADTs. Дозволити `| x -> use_x_here` як binding — і парсер не зможе розрізнити state-name від нової змінної без типової інформації. Простіше заборонити взагалі.

На практиці обмеження мало болить, бо є `let`:

```swl
let cell Tree =
  let neighbors = count Fire in
  match neighbors with
  | 0 -> Tree
  | _ -> Fire    # будь-який сусід-вогонь = ми горимо
```

Якщо вам треба прив'язати "значення, що збіглося", ви робите це через `let` **до** `match`, і у тілі гілок використовуєте те саме ім'я. Не так елегантно як у OCaml, але працює.

---

## Guards (`when` clauses)

Іноді патерн сам по собі не може виразити умову. Уявіть, що у Wolf-Sheep моделі вівця хоче "втікати від вовка, якщо вовк ближче 3 клітинок, інакше йти за травою":

```swl
let cell c =
  let dist = nearest_agent_of_type_dir Wolf 5 in
  match dist with
  | _ when dist > 0 and dist <= 3 -> move ((dist + 4) mod 8)   # тікаємо
  | _                              -> move (random_dir ())     # бродимо
```

`when expr` — це додаткова умова поверх патерна. Гілка спрацьовує, лише якщо **патерн збігся** і **guard повернув `true`**. Якщо guard повернув `false`, ми переходимо до наступної гілки — guard не затіняє інші, як це робить простий патерн.

Семантика guard в `_match_case`:

```python
matched = any(_match_pattern(p, subject) for p in case.patterns)
if not matched:
    return False
if case.guard is not None:
    guard_val = eval_expr(case.guard, ctx)
    return _ensure_bool(guard_val, case.line)
return True
```

Тут є один важливий момент, який варто запам'ятати: **guard повинен повертати `bool`**. Якщо ви випадково повернули число чи state, отримаєте `SwarmletRuntimeError("expected bool but got ...")`. Це навмисне — Swarmlet не робить truthy/falsy конверсію, як Python.

**Or-патерни і guard працюють разом**. Якщо ви пишете `| Tree | Sapling when condition -> body`, guard перевіряється **один раз** після того, як хоч один з or-патернів збігся. Тобто guard не повторюється для кожного or-патерна окремо, а застосовується до всієї гілки.

---

## Or-patterns

Or-патерн — це коли кілька патернів ділять одне тіло гілки. Замість дублювати код:

```swl
match state with
| Tree    -> Fire
| Sapling -> Fire     # дублювання
| _       -> state
```

— пишемо:

```swl
match state with
| Tree | Sapling -> Fire
| _              -> state
```

У AST це `MatchCase(patterns=[Pattern(...,'Tree'), Pattern(...,'Sapling')], guard=None, body=...)`. Інтерпретатор робить `any(_match_pattern(p, subject) for p in case.patterns)` — перший збіг виграє, тіло обчислюється один раз з тим subject-ом, що був.

Or-патерни особливо корисні разом з guard-ами, коли ви хочете "ці кілька варіантів за умови":

```swl
match state with
| Tree | Sapling when any Fire   -> Fire
| Tree | Sapling                 -> state
| _                              -> state
```

Або з числами:

```swl
match self.energy with
| 0 | 1 | 2 -> die        # критично мало
| _         -> stay
```

У OCaml or-патерни мають додатковий нюанс: якщо в них є binding-и, всі or-патерни мусять biнди ti одні й ті самі імена з одними й тими самими типами. У Swarmlet цього питання немає, бо bindings заборонені.

---

## Exhaustiveness: runtime в Swarmlet, compile-time в OCaml/Rust

Ось одна з найбільших філософських різниць між Swarmlet (як уособленням prototype-style FP) і "серйозними" мовами на кшталт OCaml чи Rust.

**OCaml/Rust перевіряють вичерпність патернів на етапі компіляції.** Якщо ви оголосили тип `type tree = Empty | Node of tree * int * tree`, і у `match` написали тільки `| Empty -> ...`, компілятор скаже: "warning: this pattern-matching is not exhaustive. Here is an example of a value that is not matched: Node (_, _, _)". У Rust це буде помилкою, не попередженням.

**Swarmlet перевіряє вичерпність на етапі виконання.** Якщо жодна гілка не збіглася, ви отримаєте `SwarmletRuntimeError("non-exhaustive match")` у момент, коли движок натрапить на не-покритий випадок. Це може статися на тіку 5000, через мільйони обчислень, у середині симуляції — і ви тільки тоді дізнаєтеся, що пропустили випадок.

Чому Swarmlet так робить? Тому що у нього немає **статичного аналізатора повноти** — і його реалізація потребувала б повноцінного типового pass-у плюс логіки роботи з обмеженою множиною cell-states. Це план на майбутнє (Stage 2B чи пізніше), але v0.1 свідомо вирішила не ускладнювати.

**Практичний наслідок**: завжди закінчуйте `match` гілкою з `_`, якщо хоч мінімально не впевнені, що покрили всі варіанти. У `forest_fire.swl` стани відомі заздалегідь (`Empty | Tree | Fire | Ash`), і, теоретично, гілки `| Empty | Tree | Fire | Ash` покривають усе — але якщо хтось завтра додасть стан `Sapling`, ви про це дізнаєтеся через runtime crash. Гілка `_ -> state` рятує від такого.

---

## Порівняння з Python: імперативний `if/elif` vs Python 3.10 `match`

Подивімося, як той самий forest fire-перехід записується трьома різними способами.

### Swarmlet

```swl
let cell Tree =
  match any Fire with
  | true  -> Fire
  | false -> Tree
```

### Python імперативно (старий стиль)

```python
def cell_tree(world, x, y):
    if any_fire_neighbor(world, x, y):
        new_state = "Fire"
    else:
        new_state = "Tree"
    return new_state
```

Проміжна змінна `new_state` — бо `if` у Python statement, не вираз. Тернарник `"Fire" if ... else "Tree"` працює для двох гілок, але швидко стає гидким при більшій кількості.

### Python 3.10+ через `match`

```python
def cell_tree(world, x, y):
    match any_fire_neighbor(world, x, y):
        case True:  return "Fire"
        case False: return "Tree"
```

Тут уже краще — справжній `match`-statement (тільки statement, не вираз — у Python `match` не повертає значення, ви все одно пишете `return` всередині). Семантика дуже близька до Swarmlet.

Python 3.10 додатково підтримує binding-патерни (`case [x, y, *rest]:`) і destructuring (`case Point(x=0, y=0):`). Ці фічі ближчі до OCaml, ніж до Swarmlet — якби v0.2 хотів додати binding-патерни, прагматична угода Python 3.10 (нижній регістр — binding, верхній з крапкою — посилання на існуючий name) була б хорошим зразком.

Підсумок: Swarmlet — це Python 3.10 `match`, тільки **як вираз** і без binding-патернів.

---

## Swarmlet-код з реальних прикладів

Подивімося, як pattern matching виглядав би у переписаному `forest_fire.swl` через `match` замість каскадних `if`-ів. Поточна реалізація використовує `if`, бо вона ідіоматичніша для двох-трьох гілок, але `match` тут теж легальний.

### Forest fire через `match`

```swl
world 100 x 100 wrap

cell states Empty | Tree | Fire | Ash

param growth_rate     = 0.001
param ignition_rate   = 0.00005
param ash_clear_rate  = 0.02

let cell c =
  match state with
  | Empty when random () < growth_rate -> Tree
  | Empty                              -> Empty
  | Tree  when any Fire                -> Fire
  | Tree  when random () < ignition_rate -> Fire
  | Tree                               -> Tree
  | Fire                               -> Ash
  | Ash   when random () < ash_clear_rate -> Empty
  | Ash                                -> Ash
  | _                                  -> state
```

Одне `match` робить роботу всіх чотирьох окремих `let cell ...` правил у оригіналі. Subject — `state`. Гілки перебираються зверху вниз з guard-ами для випадкових подій. Останній `_ -> state` — захист на майбутнє додавання станів. Дублювання `Tree` і `Empty` — через те, що нам потрібні guard-и для random-events; у OCaml тут допоміг би nested pattern, у Swarmlet простіше тримати плоско.

### Wolf-Sheep вибір напрямку

З `wolf_sheep.swl` сьогодні:

```swl
let prey_count = agents_of_type_in_radius Sheep wolf_vision in
if prey_count > 0
  then move prey_dir
  else move (random_dir ())
```

Те саме через `match`:

```swl
let prey_count = agents_of_type_in_radius Sheep wolf_vision in
match prey_count with
| 0 -> move (random_dir ())
| _ -> move prey_dir
```

Або з or-pattern для кількох "критично мало":

```swl
match self.energy with
| 0 | 1 | 2 | 3 -> seq { move (random_dir ()); die }
| _ when self.energy > wolf_repro_thresh -> spawn Wolf
| _ -> move prey_dir
```

Це показує number-patterns (`0`, `1`, `2`, `3`), or-patterns, wildcard, і guard-и в одному місці. State-name patterns тут немає, бо subject — `self.energy` (число), не state. Вони були у forest_fire вище.

### Усі 4 види патернів в одному прикладі

Для повноти — синтетичний приклад, який демонструє всі чотири патерни в одному `match`:

```swl
let cell c =
  let r = random () in
  match state with
  | Empty when r < 0.5  -> Tree         # ident-pattern + guard
  | Tree                -> Fire         # ident-pattern
  | Fire | Ash          -> Empty        # or-pattern of ident-patterns
  | _                   -> state        # wildcard
```

І окремий, що показує bool і number patterns:

```swl
let attack = any Fire in
match attack with
| true  -> Fire
| false -> Tree
```

```swl
match self.energy with
| 0       -> die
| 1 | 2   -> stay
| _       -> move (random_dir ())
```

---

## Місток до OCaml

Екскурс у те, як pattern matching виглядає в OCaml — мові, з якої Swarmlet перейняв ідею ML-стилю синтаксису. Це покаже, що **обмежено** у Swarmlet, що **спільно**, і чому повний pattern matching — настільки могутня річ, що змінює структуру програми.

### Базовий синтаксис OCaml

OCaml `match`-вирази виглядають дуже схоже:

```ocaml
match expr with
| pattern1 -> body1
| pattern2 -> body2
| _        -> body3
```

— той самий вертикальний бар, той самий `with`, той самий `->`. Swarmlet навмисно копіював синтаксис, щоб ML-бекграунд одразу впізнавав структуру.

### Algebraic Data Types (ADTs)

У OCaml ви оголошуєте власні типи з кількома конструкторами:

```ocaml
type cell_state =
  | Empty
  | Tree
  | Fire
  | Ash
```

Конструктор — варіант типу. `Empty` сам по собі — значення типу `cell_state`. Конструктори можуть мати поля:

```ocaml
type tree =
  | Leaf
  | Node of tree * int * tree

let rec sum_tree t =
  match t with
  | Leaf -> 0
  | Node (l, x, r) -> sum_tree l + x + sum_tree r
```

Тут `Node (l, x, r)` — паралельно і **discriminator** ("це Node, не Leaf"), і **destructor** ("розклади на три частини"), і **binder** ("ці частини — `l`, `x`, `r`"). Усі три ролі pattern matching в одному рядку. Swarmlet не має конструкторів-з-полями, тому destructuring і binding відсутні.

### Pattern matching як суперскладна `if/elif` ланцюгова

OCaml-ний код часто виглядає як одна довга `match`-конструкція — і це не страшно, це **природно**:

```ocaml
let classify n =
  match n with
  | 0                 -> "zero"
  | n when n < 0      -> "negative"
  | 1 | 2 | 3 | 5 | 7 -> "small prime"
  | n when n mod 2 = 0 -> "even"
  | _                 -> "odd"
```

Те саме у Swarmlet (з нюансами):

```swl
let classify n =
  match n with
  | 0                       -> 0     # "zero" — у нас немає рядків, тому числа
  | _ when n < 0            -> -1    # "negative"
  | 1 | 2 | 3 | 5 | 7       -> 1     # "small prime"
  | _ when (n mod 2) == 0   -> 2     # "even"
  | _                       -> 3     # "odd"
```

Зверніть увагу на різницю: у OCaml-нийому `n when n < 0` `n` — це binding (нове ім'я для значення), у Swarmlet ми мусимо писати `_ when n < 0`, бо `n` як binding-патерн не дозволено, але `n` як ім'я з зовнішнього скоупу (через `let n = ... in`) видно у guard-ах.

### Recursive ADTs і structural recursion

Класичний OCaml-ний приклад — список:

```ocaml
let rec length = function
  | []      -> 0
  | _ :: xs -> 1 + length xs
```

`[]` — патерн порожнього списку, `_ :: xs` — "голова (не цікавить) cons зі хвостом `xs`". Цей стиль — **structural recursion** — фундамент функціонального програмування: визначаємо функцію за структурою вхідного типу, кожна гілка обробляє один структурний випадок. У Swarmlet рекурсії й ADTs немає, тож стиль не застосовується.

### Compile-time exhaustiveness в OCaml

Якщо ви оголосили `type cell_state = Empty | Tree | Fire | Ash` і написали:

```ocaml
let next state =
  match state with
  | Empty -> Tree
  | Tree  -> Fire
```

OCaml warning **на компіляції**: `Warning 8: this pattern-matching is not exhaustive. Here is an example of a case that is not matched: (Fire | Ash)`. У Swarmlet ви отримали б `SwarmletRuntimeError` тільки тоді, коли клітинка реально перейде у стан `Fire` чи `Ash`. Це принципова різниця між статично-типізованою мовою з ADTs і динамічною без них.

### Записи (records) і destructuring

OCaml дозволяє патерн на полях запису:

```ocaml
type point = { x : int; y : int }

let origin_check p =
  match p with
  | { x = 0; y = 0 } -> "at origin"
  | { x = 0; y = _ } -> "on y-axis"
  | { x = _; y = 0 } -> "on x-axis"
  | _                -> "elsewhere"
```

Патерн `{ x = 0; y = 0 }` одразу і destructure-ить запис, і дискримінує. Swarmlet не має records, тому такого немає.

### Список паралелей

Спільне з OCaml: синтаксис `match ... with | ...`, wildcard, літеральні константи, or-patterns, guards, match-як-вираз. Відсутнє у Swarmlet v0.1: ADT constructor patterns (`Some x`, `Cons (h, t)`), variable bindings, nested patterns без дужок (SPEC 7.6), compile-time exhaustiveness check, tuple/record/list destructuring. Swarmlet взяв стиль і базовий механізм, але пропустив усе, що потребує статичної типової інформації — це робить інтерпретатор простим (~30 рядків eval) і мову вивчабельною за день.

---

## Чому це важливо на практиці

Чому pattern matching — не просто синтаксичний цукор поверх `if/elif`?

**Локальність розрізнення.** Imperative-код, який обробляє автомат, часто розкладений по диспатч-функції і окремих handler-ах:

```python
def update_cell(state, neighbors):
    if state == "Empty":   return handle_empty(neighbors)
    elif state == "Tree":  return handle_tree(neighbors)
    elif state == "Fire":  return handle_fire(neighbors)
    elif state == "Ash":   return handle_ash(neighbors)
    else: raise ValueError(f"unknown: {state}")
```

Логіка переходів розкидана по чотирьох функціях. У Swarmlet той самий код — одне `match` із гілками; кожен перехід видно в одному файлі поряд з усіма іншими. Це власне те, чим pattern matching корисний у DSL для cellular automata.

**Експресивність nested patterns.** У OCaml/Haskell patterns бувають вкладеними:

```ocaml
match expr with
| Some (Cons (1, Nil)) -> "single 1"
| Some (Cons (h, _))   -> "head is " ^ string_of_int h
| None                 -> "no list"
```

Imperative-еквівалент — 4-5 nested `if`-ів з купою `is None`. Swarmlet цього не вміє (немає nested data), але силу варто пам'ятати, коли побачите Erlang/Elixir/Scala.

**Expression problem.** OO-мови через virtual dispatch роблять легким додавання станів, але важким — додавання операцій. Pattern matching — навпаки: легко додати нову операцію (нова функція з `match`), важче додати новий варіант (треба знайти всі `match` і доповнити). Cellular automata мають **малий фіксований набір станів** і **багато операцій** — це ідеальний випадок для patterns.

---

## Поширені пастки

Чотири речі, на яких new-комеристи у Swarmlet регулярно спотикаються.

### Пастка 1: думати, що ідентифікатор у патерні — це binding

```swl
let cell c =
  match state with
  | x -> x       # ВИ ДУМАЄТЕ: збігається з будь-чим, x — нове ім'я
                 # НАСПРАВДІ: збігається тільки якщо state == "x" (state-name)
```

Якщо у вас немає cell-state з ім'ям `x`, гілка ніколи не спрацює. Якщо є — спрацює, але тільки на нього. Виправлення: використайте `_` або заведіть змінну через `let` до `match`:

```swl
let cell c =
  let s = state in
  match s with
  | _ -> s       # тепер s — це справжнє значення з let
```

### Пастка 2: забувати `_` у кінці і отримувати runtime crash

```swl
match state with
| Tree -> Fire
| Fire -> Ash
# що якщо state == Empty чи Ash?
```

На стані `Empty` отримаєте `SwarmletRuntimeError("non-exhaustive match")` — і не на компіляції, а в середині симуляції на тіку 4523. Завжди закінчуйте `match` або повним перебором всіх станів, або `_`-гілкою.

### Пастка 3: nested match без дужок

```swl
let cell Tree =
  match any Fire with
  | true  -> Fire
  | false -> match random () with         # парсер губиться
            | p when p < 0.001 -> Fire
            | _ -> Tree
```

Парсер не знає, чи `| p when ...` — це продовження зовнішнього `match` чи внутрішнього. Swarmlet вимагає явних дужок (SPEC 7.6):

```swl
let cell Tree =
  match any Fire with
  | true  -> Fire
  | false -> (match random () with
              | p when p < 0.001 -> Fire
              | _ -> Tree)
```

Краще — переписати через `let` і `if` (SPEC сама пропонує цей варіант як ідіоматичний).

### Пастка 4: guard повертає не-bool

```swl
match state with
| Tree when count Fire -> Fire    # count повертає число, не bool
| _ -> state
```

`SwarmletRuntimeError("expected bool but got number")`. Виправлення: явне порівняння.

```swl
match state with
| Tree when count Fire > 0 -> Fire
| _ -> state
```

Swarmlet суворо вимагає `bool` у guard-ах і `if` — стилістичне рішення на користь явності.

---

## Вправи

Чотири задачі, які закріпили б усе розказане. Розв'язки не наводяться — це навмисно.

### Вправа 1: переписати forest fire через `match`

**Setup**: відкрийте `swarmlet/examples/forest_fire.swl`. Поточна версія використовує чотири окремі `let cell <State>` правила з `if`-каскадами всередині.

**Завдання**: перепишіть весь файл так, щоб правила переходів виражалися одним `let cell c = match state with | ... -> ...`. Збережіть всю поведінку (growth_rate, ignition_rate, ash_clear_rate працюють як раніше).

**Підказка**: вам знадобляться guard-и для випадкових подій (`when random () < growth_rate`). Майте на увазі, що `random ()` обчислюватиметься окремо для кожного guard-у — якщо хочете гарантувати, що "одна випадкова цифра на одну клітинку", винесіть її в `let r = random () in` до `match`.

### Вправа 2: класифікація енергії агента

**Setup**: ви будуєте свою простеньку модель з агентами Wolf, у яких є поле `energy`.

**Завдання**: напишіть `match self.energy with`, який повертає один з трьох станів дій:
- `die` якщо energy ≤ 0
- `stay` якщо energy у [1, 5]
- `move (random_dir ())` якщо energy > 5

Використайте and-у guards, and or-patterns, and wildcard. Спробуйте мінімізувати кількість гілок.

**Підказка**: для діапазону [1, 5] — або `1 | 2 | 3 | 4 | 5 -> stay`, або `_ when self.energy <= 5 -> stay` (з гарантією, що попередня гілка вже впіймала ≤ 0). Друге елегантніше, але залежить від порядку.

### Вправа 3: розрізнення сусідніх станів

**Setup**: уявіть модель, де у клітинки є builtin `dominant_neighbor` (псевдо), який повертає state-ім'я найчастішого сусіда.

**Завдання**: напишіть `match dominant_neighbor with` так, щоб клітинка переймала стан більшості (Tree -> Tree, Fire -> Fire), окрім випадку, коли більшість — Ash, тоді залишайся Empty.

**Підказка**: тут ідентифікатори в патернах — це state-names. `Ash` у патерні — це порівняння з "Ash". Завершіть обов'язково wildcard-ом.

### Вправа 4: guard з or-patterns і енергією

**Setup**: модель Wolf-Sheep, повна версія.

**Завдання**: напишіть один `match self.energy with`, який покриває:
- 0, 1, 2 — die
- 3, 4, 5 — move (random_dir ())
- 6-15 — move prey_dir (агресивне полювання)
- > 15 — spawn Wolf і потім move (random_dir ())

Використайте or-patterns для перших двох випадків, guard-и для діапазонів 6-15 і > 15.

**Підказка**: пам'ятайте порядок — гілки зверху виграють. У Swarmlet немає `seq` як виразу, тому "spawn потім move" доступне тільки в agent rule-блоках через `seq { ... }`.

---

## Підсумок

Pattern matching — це **discrimination + destructuring + binding** в одному синтаксичному конструкторі. Swarmlet v0.1 використовує тільки discrimination (плюс or-patterns і guards), залишаючи destructuring і binding на майбутнє.

У Swarmlet patterns — це чотири види: `_` (wildcard), число-літерал, `true`/`false`, ім'я cell-state. Жодних binding-патернів. Жодного nested-matching без дужок. Жодної compile-time перевірки вичерпності — пропустили `_`, отримали runtime crash.

Усе це — навмисні обмеження, які роблять інтерпретатор простим (~30 рядків `_eval_match`) і навчабельним за вечір. Коли вам забракне виразності — ви будете готові до OCaml, де ті самі `match`-вирази розкриваються повністю, з конструкторами, рекурсивними ADTs і compile-time гарантіями повноти.

Головне — почати думати про код як про "трансформацію значень через discrimination на варіанти" замість "ланцюжків `if`-statement-ів з присвоюваннями". Це той ментальний зсув, після якого ви не зможете писати на Java тим самим способом, що раніше.
