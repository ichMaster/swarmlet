# Algebraic data types: коли тип — це AND або OR

Якщо ви прийшли з імперативного світу (Java, C#, Go, Python), у вас уже є хороша інтуїція про **product types** — навіть якщо ви ніколи не чули цього слова. Будь-який struct, клас з полями, namedtuple — це product type. "Об'єкт користувача містить ім'я **і** вік **і** email" — це AND-композиція. Ми збираємо менші типи в більший через кон'юнкцію.

А ось що в імперативних мовах представлено погано — це **sum types**. Ситуація "значення є **або** числом, **або** змінною, **або** додаванням, **або** множенням" — це OR-композиція. У Java для цього доводиться будувати ієрархію класів плюс instanceof; у Go — interface + type switch; у Python — isinstance-каскади або (з 3.10) `match`. Усі ці підходи — обхідні шляхи навколо того, що мова не має нативного поняття "тип-сума".

Цей документ — про те, як ADT (algebraic data types) поєднують ці дві ідеї, чому AST інтерпретатора — це канонічний приклад sum type, як ми реалізували це у Swarmlet (на Python, з усіма його обмеженнями), і як те саме виглядало б у мові з нативними ADT (OCaml, Rust, Haskell). А ще — про **exhaustiveness checking**, який є справжньою причиною любити ADT.

Документ читається разом із [expression-evaluator-explained.md](04-expression-evaluator-explained.md), [pattern-matching-explained.md](02-pattern-matching-explained.md), і [recursion-vs-iteration.md](09-recursion-vs-iteration.md) — сусідні документи з тієї ж серії "як ми думаємо про код у Swarmlet".

---

## Звідки взявся термін "algebraic"

Слово "algebraic" тут не випадкове. Якщо подивитися на типи як на множини значень, які вони можуть приймати, виходить буквальна алгебра.

Тип `bool` має 2 значення (`True`, `False`). Тип `Color = Red | Green | Blue` має 3 значення. Якщо ми зробимо product `(bool, Color)`, він матиме `2 * 3 = 6` можливих значень — звідси **product**, "добуток". А якщо ми зробимо sum `Result = Ok of int | Error of string`, він матиме `|int| + |string|` значень — звідси **sum**, "сума".

Тобто:

- **product type** = декартів добуток множин значень (`A * B`)
- **sum type** = диз'юнктне об'єднання множин значень (`A + B`)

Один тип "збирає" дані разом, інший "розрізнює" дані за категоріями. Ці дві операції — `*` і `+` — і дають назву "алгебраїчні". Із них (плюс рекурсія через посилання на той самий тип) можна збудувати будь-яку складну структуру даних.

Більшість імперативних мов реалізує `*` нативно (struct/class) і кульгає на `+`. Функціональні мови реалізують обидва нативно. Це не косметична різниця — вона змінює те, як ви проектуєте програми.

---

## Product types vs sum types: однакова мова, різні ролі

Розберімося детально на одному прикладі. Уявімо, ми моделюємо подію в системі.

### Product type: подія як набір полів

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class LoginEvent:
    user_id: int
    timestamp: float
    ip_address: str
    success: bool
```

Це product. Кожна `LoginEvent` має **усі чотири** поля — обов'язково. Якщо ми позначимо множину можливих `user_id` як `U`, timestamps як `T`, IP-адрес як `I`, bool як `B`, то множина можливих `LoginEvent` — це `U * T * I * B`. Усі комбінації допустимі.

У будь-якій імперативній мові це виражається легко. У Python це dataclass, у Java — клас з полями і конструктором, у Go — struct, у Rust — теж struct, у TypeScript — interface або type alias. Усі ці інструменти роблять одну річ: з'єднують декілька менших типів в один більший через AND.

### Sum type: подія як один з декількох варіантів

Тепер уявімо, що подія може бути різного **роду**: вхід у систему, вихід, оновлення профілю, або помилка. Кожен рід події має своє підмножина даних.

```python
@dataclass(frozen=True)
class LoginEvent:
    user_id: int
    timestamp: float
    ip_address: str

@dataclass(frozen=True)
class LogoutEvent:
    user_id: int
    timestamp: float

@dataclass(frozen=True)
class ProfileUpdateEvent:
    user_id: int
    timestamp: float
    field_changed: str
    new_value: str

@dataclass(frozen=True)
class ErrorEvent:
    timestamp: float
    error_message: str

Event = LoginEvent | LogoutEvent | ProfileUpdateEvent | ErrorEvent
```

Тепер `Event` — це sum. Конкретне значення `Event` — це **або** `LoginEvent`, **або** `LogoutEvent`, **або** `ProfileUpdateEvent`, **або** `ErrorEvent`. Не одночасно — рівно один з них. Кожен варіант — сам по собі product (має свої поля), але `Event` як ціле — sum.

Зверніть увагу на критичну річ: різні варіанти **мають різні поля**. У `LoginEvent` є `ip_address`, в `LogoutEvent` — немає. В `ErrorEvent` нема `user_id`. Спроба представити це як один великий product з усіма полями та купою `Optional` — це класичний антипатерн, який зустрічається в кодових базах, де sum types недоступні (або ними не користуються):

```python
# поганий варіант — нечітко представлений sum
@dataclass
class Event:
    kind: str  # "login" | "logout" | "profile_update" | "error"
    user_id: Optional[int] = None
    timestamp: float = 0.0
    ip_address: Optional[str] = None
    field_changed: Optional[str] = None
    new_value: Optional[str] = None
    error_message: Optional[str] = None
```

Тут sum схований за продуктом з кучею `Optional`. Інваріант "якщо `kind == 'login'`, то `ip_address` обов'язковий, а `error_message` має бути `None`" — стає невидимим. Тип системі він не відомий, а отже компілятор/IDE/static checker нічим не допоможе. Програміст має тримати його в голові, і кожен новий контриб'ютор буде його порушувати.

Sum types роблять це явним. Якщо ви тримаєте `LoginEvent`, ви точно знаєте, що в нього є `ip_address` і немає `error_message`. Тип каже все.

### Як вони комбінуються

Реальні структури даних — це майже завжди суміш sums і products. Список — це sum (`Empty | Cons of head, tail`), і кожен Cons-варіант — product (head і tail). Дерево — те саме. AST інтерпретатора — sum з варіантів (Num, Var, Add, Mul...), кожен з яких — product (Add містить лівий і правий операнди).

Є ще третя примітивна операція — рекурсивні типи (тип посилається на сам себе). У сумі з products і sums, рекурсія дає вам повну виразність для будь-яких деревовидних та списочних структур. Це і є той фундамент, на якому стоїть весь дизайн типів у функціональних мовах.

---

## Класичний приклад: вирази як sum type

Давайте перейдемо до прикладу, який ілюструє все одночасно — арифметичні вирази. Цей приклад — традиційний "Hello World" світу ADT, бо він мінімальний, але демонструє і sum, і product, і рекурсію.

Ми хочемо моделювати вирази типу `2 + x * 3`. Структурно вираз — це **одна з** таких речей:

- число (літерал, наприклад `2`)
- змінна (наприклад `x`)
- сума двох виразів
- добуток двох виразів

Ось як це виглядає у нотації ADT, мовою-нейтрально:

```
Expr = Num(value: int)
     | Var(name: string)
     | Add(left: Expr, right: Expr)
     | Mul(left: Expr, right: Expr)
```

Чотири варіанти. Перший і другий — листя (не містять інших виразів). Третій і четвертий — рекурсивні (містять інші вирази). Тепер `2 + x * 3` представляється як:

```
Add(Num(2), Mul(Var("x"), Num(3)))
```

Це дерево. Корінь — `Add`. Лівий нащадок — `Num(2)`, правий — `Mul(Var("x"), Num(3))`. І так далі. Такий тип називається **рекурсивний sum type** — sum, у якому деякі варіанти містять значення того ж типу.

Що ми хочемо робити з виразами? Принаймні дві операції:

1. **Обчислити** вираз у заданому контексті (де відомі значення змінних).
2. **Надрукувати** вираз як рядок.

Обидві операції природно пишуться через `match` по варіантах:

```
def evaluate(expr, env):
    match expr:
        case Num(v): return v
        case Var(name): return env[name]
        case Add(l, r): return evaluate(l, env) + evaluate(r, env)
        case Mul(l, r): return evaluate(l, env) * evaluate(r, env)
```

Кожен варіант обробляється окремо. Структура `evaluate` повторює структуру типу — один case на варіант, рекурсивний виклик там, де варіант рекурсивний. Це фундаментальний патерн, і він буде повторюватися в усьому, що ми пишемо у Swarmlet.

Тепер — як це виглядає чотирма різними способами в Python.

---

## Чотири способи представити sum type у Python

Python не має нативного sum type. Але є щонайменше чотири робочих підходи, кожен зі своїми компромісами. Свавлет — частина екосистеми, де варіанти AST представлені одним з цих способів (а саме — третім, sealed dataclass + isinstance).

### Спосіб 1: ієрархія класів з isinstance

```python
class Expr:
    pass

class Num(Expr):
    def __init__(self, value):
        self.value = value

class Var(Expr):
    def __init__(self, name):
        self.name = name

class Add(Expr):
    def __init__(self, left, right):
        self.left = left
        self.right = right

class Mul(Expr):
    def __init__(self, left, right):
        self.left = left
        self.right = right


def evaluate(expr, env):
    if isinstance(expr, Num):
        return expr.value
    if isinstance(expr, Var):
        return env[expr.name]
    if isinstance(expr, Add):
        return evaluate(expr.left, env) + evaluate(expr.right, env)
    if isinstance(expr, Mul):
        return evaluate(expr.left, env) * evaluate(expr.right, env)
    raise TypeError(f"unknown expression: {expr}")
```

Це найбільш "об'єктний" підхід. `Expr` — базовий клас, варіанти — підкласи. Диспатч — через `isinstance`. Працює, але:

- Багатослівно (boilerplate для конструкторів)
- Поля мутабельні за замовчуванням (можна випадково змінити вузол AST)
- Немає `__eq__` і `__hash__`, треба писати вручну
- Ієрархія "відкрита" — будь-хто може додати ще один підклас і зламати exhaustiveness припущення

Класичний об'єктно-орієнтований стиль каже: "не використовуй isinstance, додай метод `evaluate` у кожен підклас". Але це переносить логіку у тип, тоді як для багатьох операцій (друк, оптимізація, типізація, серіалізація...) логіка природно живе **зовні**, ближче до контексту виклику. Про це конфлікт ми поговоримо нижче в розділі про expression problem.

### Спосіб 2: тег + кортеж даних

```python
def evaluate(expr, env):
    tag = expr[0]
    if tag == "Num":
        return expr[1]
    if tag == "Var":
        return env[expr[1]]
    if tag == "Add":
        return evaluate(expr[1], env) + evaluate(expr[2], env)
    if tag == "Mul":
        return evaluate(expr[1], env) * evaluate(expr[2], env)
    raise TypeError(f"unknown tag: {tag}")


# Використання:
expr = ("Add", ("Num", 2), ("Mul", ("Var", "x"), ("Num", 3)))
```

Це найбільш "лісповий" стиль — все є кортеж, перший елемент — тег, решта — поля. Дуже компактно, природно серіалізується у JSON, не потребує жодних класів. Але:

- Доступ до полів по індексу (`expr[1]`, `expr[2]`) — нечитаний
- Жодної допомоги від типу — IDE нічого не підкаже
- Помилка типу `expr[3]` коли варіант має тільки два поля — runtime error
- Тег як рядок — легко зробити друкарську помилку (`"Mull"` замість `"Mul"`)

Цей стиль ще зустрічається в обробці JSON / wire-format даних, де варіант природно представлений як `{"type": "...", "data": ...}`. Але як внутрішнє представлення AST — він поганий.

### Спосіб 3: sealed dataclass з isinstance (наш вибір)

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Num:
    value: float

@dataclass(frozen=True)
class Var:
    name: str

@dataclass(frozen=True)
class Add:
    left: object
    right: object

@dataclass(frozen=True)
class Mul:
    left: object
    right: object


def evaluate(expr, env):
    if isinstance(expr, Num):
        return expr.value
    if isinstance(expr, Var):
        return env[expr.name]
    if isinstance(expr, Add):
        return evaluate(expr.left, env) + evaluate(expr.right, env)
    if isinstance(expr, Mul):
        return evaluate(expr.left, env) * evaluate(expr.right, env)
    raise TypeError(f"unknown expression: {expr}")
```

Це варіант, який ми використовуємо у Swarmlet. Подивіться на [/Users/Vitalii_Bondarenko2/development/swarmlet/swarmlet/ast.py](../swarmlet/ast.py) — там 30+ frozen dataclass, які разом утворюють sum type для всього AST. У [/Users/Vitalii_Bondarenko2/development/swarmlet/swarmlet/eval.py](../swarmlet/eval.py) — той самий isinstance-каскад в `eval_expr`.

Чому саме цей варіант:

- `frozen=True` — імутабельні значення, неможливо випадково мутувати AST
- автоматично генерує `__init__`, `__repr__`, `__eq__`, `__hash__`
- доступ до полів по імені, а не по індексу — читається як код у мові з ADT
- кожен варіант — окремий клас, а не загальний контейнер — тип сам собою щось каже

Недолік той самий, що й у способі 1: немає **жодного** способу сказати Python "ось список усіх варіантів, перевір що я обробив усі". Disptch-функція може забути варіант, і Python нічого не скаже до того моменту, поки забутий варіант не зустрінеться в runtime.

### Спосіб 4: Python 3.10 match із class patterns

```python
def evaluate(expr, env):
    match expr:
        case Num(value=v):
            return v
        case Var(name=n):
            return env[n]
        case Add(left=l, right=r):
            return evaluate(l, env) + evaluate(r, env)
        case Mul(left=l, right=r):
            return evaluate(l, env) * evaluate(r, env)
        case _:
            raise TypeError(f"unknown: {expr}")
```

Найкрасивіший Python-варіант. Class patterns у `match` дозволяють деструктурувати dataclass прямо в case — як у мові з ADT. Поля називаються по імені, рекурсія читається природно. Виглядає майже як OCaml.

Але `match` в Python 3.10+ — **не exhaustive**. Тобто якщо ви забудете case для `Mul`, Python піде у `case _` і кине помилку — у runtime, на конкретному вхідному дереві, а не у момент написання коду. Те саме, що з isinstance. Ми отримали кращий синтаксис, не отримали гарантій.

У Swarmlet ми не використовуємо `match` усередині — лише isinstance. Чому? Бо проект сумісний зі старшими Python-ами (3.9+), а ще тому що `match` додає синтаксичної магії, яка не дає виграшу в семантиці. Якщо exhaustiveness однаково перевіряється рукописним `raise`, нащо ускладнювати.

---

## Той самий AST в OCaml

Тепер подивімося, як **точнісінько** той самий AST виглядає в OCaml, де ADT — нативна частина мови. Без бойлерплейту, без isinstance, з повним статичним аналізом.

```ocaml
type expr =
  | Num of int
  | Var of string
  | Add of expr * expr
  | Mul of expr * expr

let rec evaluate env e =
  match e with
  | Num v -> v
  | Var n -> List.assoc n env
  | Add (l, r) -> evaluate env l + evaluate env r
  | Mul (l, r) -> evaluate env l * evaluate env r
```

Шість рядків на тип, шість рядків на функцію. Жодних класів, жодних init методів, жодного isinstance, жодного `case _`. Компілятор знає, що `expr` має рівно чотири варіанти, і при кожному `match` перевіряє, що вони всі присутні.

А ось як виглядав би повний sum type для AST виразів Swarmlet, з тією ж структурою, що й наша Python-реалізація:

```ocaml
type expr =
  | Num   of float
  | Bool  of bool
  | Var   of string
  | BinOp of string * expr * expr
  | UnOp  of string * expr
  | Call  of string * expr list
  | Dot   of expr * string
  | If    of expr * expr * expr
  | Let   of string * expr * expr
  | Match of expr * match_case list

and match_case = {
  patterns : pattern list;
  guard    : expr option;
  body     : expr;
}

and pattern =
  | PWildcard
  | PIdent  of string
  | PNumber of float
  | PBool   of bool
```

Помітьте кілька речей. По-перше, тут є взаємна рекурсія — `expr` посилається на `match_case`, який посилається на `expr`. Ключове слово `and` зв'язує їх в одну рекурсивну групу. По-друге, `pattern` — це власний sum type з 4 варіантами. Так само як у нашому Python `Pattern.kind` — це "wildcard", "ident", "number" або "bool" — але тут це не magic-string, а перевірений компілятором тег.

По-третє, `match_case` — це product (record). Він має три поля: `patterns`, `guard`, `body`. У OCaml records і sums — окремі конструкції, як в Rust, де є `struct` і `enum`. У Python ми все робимо через dataclass, але в OCaml це дві різні мовні форми.

Тепер evaluator:

```ocaml
let rec eval_expr ctx e =
  match e with
  | Num v          -> VNum v
  | Bool b         -> VBool b
  | Var n          -> lookup_var ctx n
  | BinOp (op, l, r) -> eval_binop ctx op l r
  | UnOp  (op, x)    -> eval_unop  ctx op x
  | Call  (f, args)  -> eval_call  ctx f args
  | Dot   (x, fld)   -> eval_dot   ctx x fld
  | If    (c, t, e)  -> if to_bool (eval_expr ctx c)
                        then eval_expr ctx t
                        else eval_expr ctx e
  | Let   (n, v, b)  -> let v' = eval_expr ctx v in
                        eval_expr (bind ctx n v') b
  | Match (s, cs)    -> eval_match ctx s cs
```

Десять варіантів — десять case-ів. Якщо завтра ми додамо `Lambda of string * expr` як новий варіант `expr`, цей `match` **не скомпілюється** — компілятор скаже "warning: this match is not exhaustive, you forgot Lambda". Це гарантія, яку Python не може дати ніяк.

Це не магія. Компілятор просто знає тип `expr`, знає що його варіантів — рівно ті, що оголошені в `type expr = ...`, і при `match` перевіряє, що всі вони обробляються. Ця проста властивість виявляється однією з найцінніших речей у системі типів взагалі.

---

## Exhaustiveness checking — головна фіча

Уявімо реальний робочий день. У вас є інтерпретатор з 30+ варіантами AST і 5+ функцій, що по них дисптчать (evaluator, аналізатор, pretty-printer, type-checker, оптимізатор...). Хтось додає новий варіант — наприклад, `Lambda` для лямбда-виразів. Що станеться?

В OCaml/Rust/Haskell:

- компілятор негайно показує **усі** функції, які роблять `match` по `expr` і не обробляють `Lambda`
- ви проходите цей список, додаєте case в кожну
- компілятор дає green light — програма знову коректно типізована
- **жоден** забутий case не пройде в продакшен

В Python:

- ви додаєте новий варіант, евентуально додаєте case в evaluator
- забуваєте додати case в pretty-printer і в analyzer
- pytest проходить — бо тести не вживають `Lambda` всюди
- через 3 тижні, у продакшені, кидається `TypeError: unknown expression`
- ви відкриваєте трасування, бачите, що pretty-printer не знає `Lambda`, виправляєте
- через ще 2 тижні той самий sequence з analyzer

Це не проблема Python як мови — це проблема представлення sum types без exhaustive check. Будь-яка мова, де варіанти sum-у "відкриті" (можна додати ззовні) і немає компіляторної перевірки покриття, страждає від цього.

Як це виглядає в OCaml практично:

```ocaml
let rec pretty e =
  match e with
  | Num v -> string_of_float v
  | Var n -> n
  | Add (l, r) -> pretty l ^ " + " ^ pretty r
  (* забув Mul! *)
```

Компілятор:

```
Warning 8: this pattern-matching is not exhaustive.
Here is an example of a case that is not matched:
Mul (_, _)
```

Якщо warnings включені як errors (`-w +a -warn-error +a`, що є стандартом для серйозних OCaml-проектів), компіляція провалюється. Програма не дійде до тестів — її не дозволять запустити.

В Rust те саме, з тим самим механізмом:

```rust
enum Expr {
    Num(f64),
    Var(String),
    Add(Box<Expr>, Box<Expr>),
    Mul(Box<Expr>, Box<Expr>),
}

fn pretty(e: &Expr) -> String {
    match e {
        Expr::Num(v) => v.to_string(),
        Expr::Var(n) => n.clone(),
        Expr::Add(l, r) => format!("{} + {}", pretty(l), pretty(r)),
        // забув Mul!
    }
}
```

Компілятор Rust:

```
error[E0004]: non-exhaustive patterns: `Mul(_, _)` not covered
```

Не warning — **error**. Програма не скомпілюється. Без обхідних шляхів.

Це і є той виграш, заради якого варто терпіти всі інші особливості функціональної типізації. Один раз додати варіант — і компілятор сам проводить вас усім кодом, показуючи всі місця, які треба оновити. У великій кодовій базі це різниця між "рефакторинг — це ризик" і "рефакторинг — це механічна процедура".

---

## Чому Python не може зробити це добре

Можна було б очікувати, що додавання `match` у Python 3.10 принесе exhaustiveness check. Не принесло, і причини глибокі.

По-перше, **Python динамічний**. Базовий клас `Expr` (або просто object, як у нас в Swarmlet) — це **відкритий** тип. Будь-який код у будь-якому модулі може створити новий підклас (`class MyCustomNode(Expr)`) і передати його у evaluator. Компілятор не може знати наперед, які підкласи є.

По-друге, **система типів Python — опціональна**. `mypy` і `pyright` — зовнішні інструменти, не частина мови. Вони можуть зробити exhaustiveness check у деяких випадках (з `Literal` types, з `typing.Final`, через `Union[...]`), але:

- Тільки якщо ви не змішуєте з `object` або untyped кодом
- Тільки на типи, які вони бачать статично
- Тільки якщо ви запускаєте лінтер у CI і ставитеся до його warnings серйозно

По-третє, **`match` в Python — динамічний**. `case _` завжди допустимий, і його часто додають "для безпеки", що знищує можливість будь-якої статичної перевірки покриття. Ба більше, class patterns в `match` не вимагають, щоб класи знаходилися в одному типовому ієрархічному дереві.

Що ми робимо натомість у Swarmlet? Стандартний Python-ідіом для "мав покрити все, але провалився":

```python
def eval_expr(node, ctx):
    if isinstance(node, A.Num):
        return node.value
    if isinstance(node, A.Var):
        return _eval_var(node, ctx)
    # ... ще 10 варіантів ...
    raise SwarmletRuntimeError(
        f"unhandled expression node: {type(node).__name__}",
        line=getattr(node, "line", 0),
    )
```

Останній `raise` — це ваш runtime "exhaustiveness" check. Коли він стрельне, ви знатимете, що пропустили варіант. Альтернативно у багатьох кодових базах пишуть:

```python
assert False, f"unreachable: {node!r}"
```

Це працює, але має один поганий нюанс — `assert` вимикається під `python -O`, тож для production-коду краще явний `raise`. У Swarmlet ми кидаємо типізовану помилку через `SwarmletRuntimeError`, яка має правильний line number і інтегрується із системою помилок проекту.

Сухий висновок: у Python ми **симулюємо** ADT через дисципліну (frozen dataclasses, isinstance, raise при пропуску), але без компіляторної підтримки. Кожен новий варіант — це відповідальність розробника. Тести покривають частину, але не все. Це працює на проекті розміру Swarmlet, але масштабується погано — і саме тому великі інтерпретатори часто пишуть на OCaml або Rust, а не на Python.

---

## Products комбінують, sums розрізнюють

Ще одна ментальна модель, яка допомагає. Коли ви бачите тип, спитайте себе: "це AND чи OR?".

**Product** комбінує. У нього є все, що в нього оголошено — одночасно. Якщо ви маєте `Add { left: Expr, right: Expr }`, у вас є **і** ліва, **і** права частина. Доступ до обох безумовний — `add.left`, `add.right`.

**Sum** розрізнює. Він є чимось одним з декількох. Якщо у вас `Expr = Num | Var | Add | Mul`, у вас точно **один** з чотирьох. Перш ніж дістатися до полів, потрібно з'ясувати, **який саме** — через pattern match або isinstance.

З цього випливає практичне правило: **products читаються, sums дисптчаться**. Поле product-а — це просто `obj.field`. Поле sum-а — це завжди питання "перевірити варіант, потім дістати".

Ще одне практичне правило: **products розширюються "у ширину", sums розширюються "у довжину"**. Додати поле в product — це додати один новий стовпчик до існуючої таблиці значень. Додати варіант у sum — це додати новий рядок (новий тип значень). Це різні операції з різними інженерними наслідками, і вони, як ми побачимо в наступному розділі, торгуються один з одним.

У Swarmlet кожен AST-вузол — це product (frozen dataclass з полями). Усі AST-вузли разом утворюють один великий sum (об'єднання всіх класів через спільну роль "AST nodes"). Дисптч у evaluator — це OR-логіка по варіантах, всередині кожного варіанту — AND-логіка по полях.

---

## Expression problem (коротко)

Існує класична дилема, яку Філіп Уодлер сформулював у 1998 році: вона називається **expression problem**.

Сценарій. Ви маєте структуру даних з декількома варіантами (`Expr` з варіантами `Num`, `Var`, `Add`, `Mul`) і декілька операцій над нею (`evaluate`, `pretty`, `simplify`). Усе разом — це матриця: рядки — варіанти, стовпчики — операції.

```
              evaluate    pretty    simplify
   Num         [code]    [code]    [code]
   Var         [code]    [code]    [code]
   Add         [code]    [code]    [code]
   Mul         [code]    [code]    [code]
```

Питання: як організувати код так, щоб **легко** додавати **і** нові рядки (нові варіанти), **і** нові стовпчики (нові операції), **без** перекомпіляції існуючого коду і **зі статичною перевіркою**?

Ось у чому фіксація:

- **Об'єктно-орієнтований підхід** — клас на варіант, метод на операцію. Додати **варіант** легко (новий клас з усіма методами), додати **операцію** важко (треба додати метод в усі існуючі класи). OO виграє у "вертикалі", програє у "горизонталі".
- **ADT/функціональний підхід** — sum type на варіанти, функція на операцію (з match). Додати **операцію** легко (нова функція з match), додати **варіант** важко (треба оновити **всі** існуючі функції). ADT виграє у "горизонталі", програє у "вертикалі".

Ці два світи — дзеркальні. Жоден не дає того й іншого нативно. Існують гібридні рішення (visitor pattern, type classes, multimethods, OCaml polymorphic variants, Rust traits з default implementations), але кожне з них має свої компроміси.

У Swarmlet ми обрали ADT-стиль (sum type + диспатч-функція), бо:

- Інтерпретатор зростає у "горизонталі" — нові операції (analyzer, evaluator, pretty-printer, можливо optimizer) додаються частіше, ніж нові варіанти AST
- Граматика мови досить стабільна — варіанти AST не міняються щотижня
- Ми все одно платимо exhaustiveness вручну (через `raise`), але ціна додавання операції в ADT-стилі — рівно одна нова функція, тоді як у OO це 30+ нових методів

Якби ми будували систему, де варіанти AST міняються частіше, ніж операції (наприклад, якби розширювали мову плагінами від користувачів), OO-підхід міг би виграти. Це інженерний trade-off, не релігія.

---

## Поширені пастки

### 1. Sum, схований за полем-тегом і Optionals

Антипатерн, який я вже згадував у розділі про продукти і суми. Виглядає так:

```python
@dataclass
class Node:
    kind: str
    name: Optional[str] = None
    value: Optional[float] = None
    left: Optional["Node"] = None
    right: Optional["Node"] = None
```

Один тип `Node` намагається представити кілька варіантів через рядок `kind` і купу опціональних полів. Це втрачає всі переваги типу: IDE не знає, які поля є валідними для якого `kind`, програміст має тримати інваріанти в голові, статичний аналізатор не допоможе. Замість цього — **окремий клас на варіант**. У Swarmlet ми це робимо послідовно: 30+ окремих frozen dataclass, без жодного "загального" класу з опціональними полями.

### 2. "Просто додам метод у базовий клас"

Спокуса: "якщо у мене вже є `Expr` як базовий клас, дайте я додам метод `evaluate` і нехай кожен підклас його перевизначає". Виглядає елегантно. Проблема: ви тягнете *усю* логіку обчислення в AST-модуль. AST починає залежати від рантайму, від контексту обчислення, від типів значень. Через місяць ви хочете додати pretty-printer — і думаєте "а нехай теж буде методом!". І ще optimizer. І ще type-checker. У результаті AST-модуль стає мегакласом з купою відповідальностей, і його тести стають важкими, бо щоб тестувати pretty-printer, треба інстанціювати половину рантайму.

Краще: тримати AST **чистими даними**, а кожну операцію — **окремою функцією зовні**. У Swarmlet `ast.py` нічого не знає про обчислення; `eval.py` нічого не знає про друк; `analyzer.py` нічого не знає про обидва. Кожен модуль має одну відповідальність.

### 3. Забутий exhaustiveness check у dispatch

Найбільш ризикована пастка для нашого Python-коду. Ви пишете dispatch:

```python
def pretty(node):
    if isinstance(node, A.Num):
        return str(node.value)
    if isinstance(node, A.Var):
        return node.name
    if isinstance(node, A.BinOp):
        return f"{pretty(node.left)} {node.op} {pretty(node.right)}"
    return ""  # <-- беззвучний дефолт
```

Помилка тут — `return ""` для "невідомих" вузлів. Якщо колись ви забудете case (наприклад, `Match`), ця функція мовчки поверне порожній рядок. Жодного винятку, жодного логу — просто неправильні дані. Дебажити це жахливо.

Завжди робіть **гучний** провал:

```python
def pretty(node):
    if isinstance(node, A.Num):
        return str(node.value)
    if isinstance(node, A.Var):
        return node.name
    if isinstance(node, A.BinOp):
        return f"{pretty(node.left)} {node.op} {pretty(node.right)}"
    raise TypeError(f"pretty: unhandled node {type(node).__name__}")
```

Якщо помилка — нехай впаде одразу, з зрозумілим повідомленням. Це — мінімальна заміна exhaustiveness check, яка все ж щось дає.

---

## Вправи

### Вправа 1: розширення AST новим варіантом

**Налаштування.** Візьміть мінімальний AST виразів:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Num:
    value: float

@dataclass(frozen=True)
class Var:
    name: str

@dataclass(frozen=True)
class Add:
    left: object
    right: object

def evaluate(e, env):
    if isinstance(e, Num):
        return e.value
    if isinstance(e, Var):
        return env[e.name]
    if isinstance(e, Add):
        return evaluate(e.left, env) + evaluate(e.right, env)
    raise TypeError(f"unhandled: {e}")
```

**Завдання.** Додайте варіант `Sub` (віднімання) і випишіть, **які саме файли/функції** довелося б оновити, якби це була повноцінна Swarmlet-кодова база (підказка: подивіться структуру `swarmlet/`). Скільки місць?

**Підказка.** У реальному Swarmlet вам довелося б торкнутися щонайменше: `lexer.py` (новий токен `-`), `parser.py` (новий precedence-level або розширення BinOp), `ast.py` (можливо новий клас, якщо це не `BinOp`), `analyzer.py` (перевірка типів), `eval.py` (case у `_eval_binop`), і тестів для всіх перерахованих. У OCaml-проекті типу того, що ми бачили вище, компілятор сам провів би вас усім списком. Додайте у вашу версію `assert False`-style "exhaustiveness" raise і подивіться, як він спрацює, якщо ви забудете case у `evaluate`.

### Вправа 2: переписати Спосіб 1 у Спосіб 4

**Налаштування.** Візьміть код зі "Способу 1: ієрархія класів з isinstance" вище.

**Завдання.** Перепишіть його у "Спосіб 4: Python 3.10 match із class patterns". Замість isinstance-каскаду використовуйте `match expr:` з `case Num(value=v):` тощо. Зверніть увагу, що для `match` з class patterns dataclass має бути визначений з полями (а не з ручним `__init__`), тож вам, можливо, доведеться спочатку конвертувати класи у dataclass.

**Підказка.** Class pattern `case Add(left=l, right=r):` працює тільки тому, що dataclass має автоматично згенеровані метадані про поля. Звичайний клас з `__init__(self, left, right)` потребуватиме явного `__match_args__ = ("left", "right")` для позиційного синтаксису `case Add(l, r):`.

### Вправа 3: знайти sum, схований у вашому коді

**Налаштування.** Відкрийте будь-яку імперативну кодову базу, з якою ви зараз працюєте (необов'язково Swarmlet — будь-яка Java/Python/Go).

**Завдання.** Знайдіть клас або структуру, у якої є поле типу "тег" (рядок або enum) і кілька опціональних полів, які мають значення лише за певних значень тега. Це — sum type, що ховається у продукті. Перепишіть його як справжній sum (через ієрархію класів або через декілька окремих dataclass). Запишіть, скільки інваріантів стало явними замість того, щоб бути непомітними.

**Підказка.** Найчастіше такі sum-и зустрічаються в типах подій (event types), станах state machine ("status" поле з різними наборами обов'язкових полів для різних статусів), результатах операцій (success/error з різними полями), у JSON DTO ("type" поле з полем-залежностями).

### Вправа 4: експеримент з OCaml

**Налаштування.** Встановіть OCaml (`brew install ocaml` на Mac, `apt install ocaml` на Linux). Або просто відкрийте https://try.ocamlpro.com — це REPL у браузері, нічого не треба ставити.

**Завдання.** Перепишіть мінімальний AST з вправи 1 на OCaml — і evaluator теж. Подивіться, скільки рядків вийшло. Тепер забудьте один варіант у `match` і подивіться на повідомлення компілятора. Тепер додайте `Sub` у тип і знову запустіть — компілятор покаже вам функції, які треба оновити.

**Підказка.** Мінімальна структура:

```ocaml
type expr =
  | Num of int
  | Var of string
  | Add of expr * expr

let rec evaluate env e =
  match e with
  | Num v -> v
  | Var n -> List.assoc n env
  | Add (l, r) -> evaluate env l + evaluate env r

let example = Add (Num 2, Var "x")
let result = evaluate [("x", 3)] example
let () = print_int result
```

Збережіть як `expr.ml`, запустіть `ocaml expr.ml`. Очікуваний вихід: `5`. Тепер експериментуйте — додайте `Mul`, заберіть варіант, забудьте case у match. Подивіться, як компілятор реагує. Це вправа на 30 хвилин, яка дасть вам відчуття того, чого Python не має.

---

## Підсумок

Algebraic data types — це формалізація двох простих ідей: тип, що поєднує (product, AND), і тип, що розрізнює (sum, OR). Імперативні мови вміють перше нативно і кульгають на другому. Функціональні — обидва.

У Swarmlet ми реалізували повноцінний sum type для AST через дисципліну: 30+ frozen dataclass у [ast.py](../swarmlet/ast.py) і isinstance-каскади у [eval.py](../swarmlet/eval.py) (та інших модулях, що оперують AST). Це працює, але платимо exhaustiveness вручну — через явні `raise` у дисптч-функціях. У OCaml/Rust той самий код був би коротший і безпечніший, бо компілятор перевірив би всі case-и автоматично.

Найважливіше, що варто винести: **коли проектуєте тип, спитайте себе — це AND чи OR?**. Якщо AND — це продукт, dataclass/struct/class. Якщо OR — це сума, ієрархія класів або (краще) набір окремих frozen dataclass з диспатчем зовні. І ніколи не змішуйте їх через "тег + опціональні поля" — це втрачає переваги типу і програмує вас у скрутне положення.

Прочитайте далі: [expression-evaluator-explained.md](04-expression-evaluator-explained.md) — як цей AST реально обробляється всередині `eval.py`. [pattern-matching-explained.md](02-pattern-matching-explained.md) — як patterns працюють у самій мові Swarmlet, не у Python-реалізації. [recursion-vs-iteration.md](09-recursion-vs-iteration.md) — про те, чому рекурсивні sum types природно обробляються рекурсивними функціями.
