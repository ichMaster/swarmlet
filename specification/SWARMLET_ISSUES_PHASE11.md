# Swarmlet Stage 1 — Phase 11 Addendum: Educational Documentation

This addendum extends `SWARMLET_ISSUES.md` with a new phase dedicated to educational documentation. The goal of Phase 11 is to make Swarmlet a **learning vehicle for functional programming**, not just a working interpreter. Each document explains one concept of FP using concrete code from the Swarmlet implementation, with parallel OCaml snippets ("OCaml-bridge" style) so the reader can transfer the intuition to the broader ML family.

The audience is the project author (Vitalii) — a senior data-engineering practitioner with ~30 years of imperative experience and no prior ML-family exposure. Documents must be in **Ukrainian**, written in the style of `minilog/docs/prolog-engine-explained.md` (conversational explanatory prose, no academic jargon, no emoji, concrete code examples). Each document is ~400-700 lines.

## Issues Summary Table — Phase 11

| # | ID | Title | Size | Tier | Read before issue |
|---|---|---|---|---|---|
| 27 | SWARMLET-027 | Doc: how to think functionally | M | 1 — Foundations | SWARMLET-001 |
| 28 | SWARMLET-028 | Doc: pattern matching as a replacement for if/elif | M | 1 — Foundations | SWARMLET-006 |
| 29 | SWARMLET-029 | Doc: let-expressions vs assignments | M | 1 — Foundations | SWARMLET-006 |
| 30 | SWARMLET-030 | Doc: how the expression evaluator works | M | 2 — Architecture | SWARMLET-011 |
| 31 | SWARMLET-031 | Doc: tick as a snapshot transformation | M | 2 — Architecture | SWARMLET-016, SWARMLET-017 |
| 32 | SWARMLET-032 | Doc: the intent pattern | M | 2 — Architecture | SWARMLET-015 |
| 33 | SWARMLET-033 | Doc: recursion vs iteration | M | 3 — Deeper | SWARMLET-024 |
| 34 | SWARMLET-034 | Doc: purity and side effects | M | 3 — Deeper | SWARMLET-024 |
| 35 | SWARMLET-035 | Doc: algebraic data types and tagged unions | M | 3 — Deeper | SWARMLET-024 |
| 36 | SWARMLET-036 | Doc: from Swarmlet to Protelis (aggregate programming bridge) | M | 4 — Bridges | SWARMLET-024 |
| 37 | SWARMLET-037 | Doc: Swarmlet and Codex axioms (cross-project bridge) | S | 4 — Bridges | SWARMLET-024 |
| 38 | SWARMLET-038 | Cheatsheet: Swarmlet syntax one-pager | S | 4 — Bridges | SWARMLET-024 |

**Size legend:** S = ≤ 0.5 day, M = 0.5–1 day, L = 1–2 days

**Total Phase 11 effort:** ~9-12 days for one author writing alone, or ~5-7 days if Claude Code does the drafting and the author reviews. Documents do NOT block the implementation issues — they can be written in parallel with implementation, or in a dedicated documentation sprint after Phase 9 completes.

---

## Recommended reading schedule

The educational documents are most useful when read **before or during** the corresponding implementation issue. The following schedule pairs each implementation milestone with the documents to read at that point:

| Before implementing | Read these documents |
|---|---|
| SWARMLET-001 (start of project) | SWARMLET-027 (FP mental model) |
| SWARMLET-006 (parser: expressions) | SWARMLET-028 (pattern matching), SWARMLET-029 (let expressions) |
| SWARMLET-011 (expression evaluator) | SWARMLET-030 (evaluator), SWARMLET-035 (ADTs) |
| SWARMLET-015 (action evaluator) | SWARMLET-032 (intent pattern) |
| SWARMLET-016, SWARMLET-017 (tick phases) | SWARMLET-031 (tick as transformation), SWARMLET-034 (purity) |
| After SWARMLET-024 (working v0.1) | SWARMLET-033 (recursion), SWARMLET-036 (Protelis bridge), SWARMLET-037 (Codex bridge) |
| Anytime as reference | SWARMLET-038 (cheatsheet) |

Following this schedule turns the project from "implement spec from issues" into "read concept → implement → see concept work in your hands → next concept" — the standard learning loop for any new paradigm.

---

## Style and structure conventions for all Phase 11 documents

Every Phase 11 document MUST follow these conventions to maintain consistency across the series:

**Language and tone:**
- Ukrainian throughout, English allowed for technical terms (function, expression, AST, etc.)
- Conversational, explanatory, written as if speaking to one person at a coffee table
- No emoji anywhere
- No academic jargon without explanation
- Style reference: `/Users/Vitalii_Bondarenko2/development/minilog/docs/prolog-engine-explained.md`

**Structure (in order):**

1. **Opening framing** (~50-100 lines) — what this document is about, why it matters, what concrete pain point it solves for an imperative-mindset reader
2. **The core concept explained from scratch** (~150-200 lines) — present the concept without assuming prior FP knowledge, build intuition with one running example
3. **Swarmlet code that exhibits the concept** (~100-150 lines) — show actual code from the Swarmlet implementation or examples, walk through it line by line
4. **OCaml-bridge section** (~80-120 lines) — show the same concept in real OCaml syntax with a parallel snippet. Explain the small differences. Goal: by the end the reader could read OCaml tutorials with this concept and not be confused
5. **Why this matters in practice** (~50-100 lines) — concrete consequences: testing, debugging, performance, scalability, code reasoning
6. **Common pitfalls** (~30-50 lines) — what an imperative-minded programmer typically gets wrong when first using this concept
7. **Exercises** (3-5 short exercises, ~50-100 lines) — small modifications the reader can try in their head or on paper. Each exercise has: setup, task, hint paragraph (collapsible if rendered to HTML, otherwise just visually separated)
8. **Summary** (~20-30 lines) — one paragraph TL;DR

**Code conventions:**

- All Swarmlet code snippets must be valid against `SPEC.md`. If a snippet does not parse or evaluate per the spec, the test in the corresponding implementation issue will catch it
- All OCaml code snippets must be valid OCaml that compiles in `ocaml` REPL (testing this is on the document author, not part of the project test suite)
- Code blocks have language hints in fences: ` ```swl`, ` ```ocaml`, ` ```python`
- Inline code uses backticks
- Variable names in prose are in backticks
- Type names like `Tree`, `Empty` are in backticks when discussing them as identifiers, plain when discussing the concept

**Cross-reference conventions:**

- Each document links to:
  - `SPEC.md` sections it explains
  - The implementation issue(s) it accompanies
  - Other Phase 11 documents it depends on (read in order)
- Cross-links are relative paths: `[SPEC.md section 7.4](../SPEC.md#74-pattern-matching-semantics)`

**File location:**
All Phase 11 documents are saved to `swarmlet/docs/` in the project repo, alongside the existing `quickstart.md` and `api.md` (which are written in SWARMLET-026).

---

## Phase 11 — Tier 1: Foundations

### SWARMLET-027 — Doc: how to think functionally

**Description:**
Write the foundational document that bridges imperative and functional thinking. This is the first document in the series and the one that should be read before any implementation begins. It uses the forest fire example to show three versions of the same logic side by side: imperative Python, Swarmlet, and OCaml. The goal is to make the reader **see** the difference between "modify in place" and "compute new from old" with their own eyes, not just hear it as theory.

**What needs to be done:**

Create `swarmlet/docs/fp-mental-model.md` covering:

- **Opening:** establish the situation — the reader is a senior imperative practitioner who needs to learn FP through this project. Explain that FP is not a "different opinion about the same thing" but a different coordinate system for the same underlying reality
- **Three versions of forest fire side by side:** imperative Python (~30 lines, with explicit nested loops, `new_grid` buffer, prapor `has_fire_neighbor`, `% width` boundary handling), Swarmlet (~10 lines), real OCaml (~15 lines). All three implement the same model. Discuss what disappeared from the functional versions and where it went (into the universal interpreter code, written once)
- **First principle: values instead of mutations.** Explain immutability through the concrete pitfall of in-place mutation in CA: a buggy Python version that writes to `grid` while reading from it, illustrating why race-in-time is real. Show how Swarmlet makes this category of bug impossible by construction
- **Second principle: expressions instead of statements.** Compare a Python `if/elif/else` block that assigns to `result` and then `return`s with the OCaml/Swarmlet version where `if/then/else` IS the expression. Discuss expression composition vs statement sequencing
- **Third principle: data flow instead of control flow.** Use the Gray-Scott example with its chain of `let cu = ... in let cv = ... in ...` as the canonical functional shape. Show that the same code in Python looks essentially identical when written without mutations, observing that "math expressions" are already functional in any language — FP just says "do this all the time"
- **Fourth principle: recursion instead of loops.** Briefly introduce the idea, with a small `sum_list` example in OCaml and Python. Note that Swarmlet v0.1 does not expose user-level recursion (no user-defined functions) but the interpreter itself uses recursion everywhere — and the reader will see this when they implement `eval_expr` in SWARMLET-011
- **What this means in practice:** a list of habits to consciously break (declare-then-assign, sequence-of-steps, if/elif chains, mutate-to-avoid-copying, global state)
- **Why it's worth pushing through:** concrete payoffs (parallelism, testing, debugging, reasoning, DSL design). Tie the last point specifically to Vitalii's migVisor work and his interest in spec-driven development
- **Exercises:** 4 exercises:
  1. Take a 3-line Python `for` loop with a counter and rewrite it as a list comprehension (warmup, no Swarmlet involved)
  2. Take the imperative forest fire from this document and identify exactly which lines disappear when you switch to Swarmlet, and where they "go to" in the interpreter you'll write
  3. Predict: if you wrote two cell rules where rule 1 reads `field pheromone` and rule 2 writes `set pheromone = ...`, would rule 2's write affect rule 1's read in the same tick? Why?
  4. Sketch (on paper) what the dependency graph of the Gray-Scott `let` chain looks like. Mark which `let` bindings are independent and could be computed in parallel

**Dependencies:** SWARMLET-001 (project must exist for the document to make sense as part of it; no implementation issues need to be done first because this document is read before everything else)

**Expected result:**
A foundational document that converts a pure imperative reader's mental model enough to make the rest of the implementation issues legible. After reading this, the reader should not be confused by `let cell Tree = ... in ...` syntax even before reading the spec in detail.

**Acceptance criteria:**
- [ ] File exists at `swarmlet/docs/fp-mental-model.md`
- [ ] Length 400-700 lines
- [ ] All three forest fire versions (Python, Swarmlet, OCaml) are present and compile/parse against their respective grammars
- [ ] Four principles are covered with at least one concrete code example each
- [ ] Habits-to-break section has at least 6 items
- [ ] 4 exercises present, each with setup + task + hint
- [ ] Cross-links to `SPEC.md` and to subsequent Phase 11 documents work
- [ ] No emoji
- [ ] Style matches `prolog-engine-explained.md` (verified by spot-check: paragraph structure, no headers every 3 lines, conversational tone)

---

### SWARMLET-028 — Doc: pattern matching as a replacement for if/elif

**Description:**
Write the document that explains pattern matching as the killer feature of the ML family — the thing that makes "functional with pattern matching" actually feel different from "if/elif chains in Python". Uses the forest fire and predator-prey examples from the spec. Walks through patterns, guards, or-patterns, and exhaustiveness checking. Shows how the same logic in Python looks worse, and how it looks identical in real OCaml.

**What needs to be done:**

Create `swarmlet/docs/pattern-matching-explained.md` covering:

- **Opening:** the reader has seen `match ... with | ... ->` in the spec and probably wondered "what's wrong with if/elif?". Promise to convert them
- **What pattern matching actually is:** a single construct that combines three things into one — destructuring (taking a value apart), discrimination (checking which case it falls into), and binding (giving names to the parts). In imperative languages these are three separate things; in FP they merge
- **The minimal example:** Swarmlet `match` on a cell state with three cases. Show the AST that this produces (one `Match` node with three `MatchCase`s). Walk through how the evaluator processes it: try case 1, if pattern matches and guard holds, evaluate body; otherwise try case 2; etc.
- **Patterns in v0.1:** wildcard `_`, literal numbers, true/false, state-name identifiers. Why state-name identifiers are NOT variable bindings in patterns (a deliberate restriction explained in the spec — discuss WHY this restriction is good for v0.1: it removes the type-pass requirement)
- **Guards with `when`:** the canonical use case is probabilistic rules in CA. Show the forest fire idiom `let cell Tree = match any Fire with | true -> Fire | false -> ...`. Discuss when guards are clearer than nested ifs and when they're not
- **Or-patterns:** `| Tree | Sapling -> Tree`. Explain why this exists (DRY), when to use it, when to use a wildcard with a guard instead
- **Exhaustiveness:** in v0.1 we don't statically check exhaustiveness, so a missing wildcard becomes a runtime error. Explain the cost of this and how real OCaml/Rust do it differently (compile-time check). Note: in Swarmlet, a missing wildcard surfaces during the run; in real ML, the compiler refuses to compile your code without all cases handled
- **The Python comparison:** show two versions of the same Tree rule:
  ```python
  if cell == "Tree":
      if has_fire_neighbor:
          new_state = "Fire"
      elif random() < 0.00005:
          new_state = "Fire"
      else:
          new_state = "Tree"
  ```
  vs Python 3.10+ `match`:
  ```python
  match cell, has_fire_neighbor, random() < 0.00005:
      case "Tree", True, _:
          new_state = "Fire"
      case "Tree", _, True:
          new_state = "Fire"
      case "Tree", _, _:
          new_state = "Tree"
  ```
  Note that Python 3.10 added `match` precisely because the FP community spent decades demonstrating its value. Discuss differences: Python's `match` allows variable binding patterns, Swarmlet v0.1 does not
- **The real OCaml version** of the Tree rule, showing how the syntax is essentially the same as Swarmlet's
- **Common pitfalls:**
  - Forgetting `_` and getting a runtime error on a value you didn't expect
  - Putting cases in the wrong order so a more specific case is shadowed by a more general one earlier
  - Using `match` for boolean conditions where `if` is shorter
  - Trying to use an identifier as a binding pattern (a v0.2 feature, not in v0.1)
- **Exercises:** 4 exercises:
  1. Rewrite this nested if from a buggy Tree rule using `match`
  2. Add a guard that says "Tree becomes Fire with probability 1.0 if the temperature field exceeds 50, otherwise the normal rule applies". Where does the guard go?
  3. Write the Predator-Prey wolf rule's "is sheep nearby" logic as a `match` expression on a tuple `(prey_count > 0, self.energy)` with three cases
  4. Why does the spec say "leading `|` is required"? What syntactic ambiguity does this prevent?

**Dependencies:** SWARMLET-006 (parser for expressions and pattern matching must be implemented before the document can show working examples that the reader can run)

**Expected result:**
A document that lets a Python-experienced reader write idiomatic Swarmlet `match` expressions confidently after one read.

**Acceptance criteria:**
- [ ] File exists at `swarmlet/docs/pattern-matching-explained.md`
- [ ] Length 400-700 lines
- [ ] At least 5 code examples (Swarmlet, OCaml, Python imperative, Python `match`, and one comparison side-by-side)
- [ ] All 4 patterns from v0.1 (wildcard, number literal, bool literal, state-name identifier) are demonstrated
- [ ] Guards and or-patterns each have a dedicated subsection
- [ ] OCaml-bridge section is at least 80 lines
- [ ] 4 exercises with hints
- [ ] No emoji
- [ ] Cross-link to SPEC.md section 7.4

---

### SWARMLET-029 — Doc: let-expressions vs assignments

**Description:**
Write the document that explains the second-biggest shock for an imperative reader: `let x = 5 in <expression>` is not assignment to a variable, it is a binding inside a scope. Cover lexical scoping, immutability, shadowing, and the chain-of-lets idiom from Gray-Scott. Show how this concept enables expressions to be composed cleanly.

**What needs to be done:**

Create `swarmlet/docs/let-expressions-vs-variables.md` covering:

- **Opening:** the reader has seen `let x = 5 in y * x` and probably parsed it as "set x to 5, then return y times x". Tell them this parsing is wrong, and a slightly different one is right
- **The core distinction:** `x = 5` in Python is a **statement** that creates or mutates a variable in some scope. `let x = 5 in expr` in Swarmlet/OCaml is an **expression** that introduces a binding visible only inside `expr` and evaluates to the value of `expr`. The first is about modifying memory; the second is about naming subexpressions for clarity
- **Lexical scoping:** the binding is visible **only** in the body, nowhere else. After the body completes, the binding is gone. This is the same scoping that Python uses for function parameters and local variables — but in Swarmlet, every name is scoped this way, there are no module-level mutable variables
- **Immutability:** within the scope where `x` is bound, `x` always means the same thing. There is no `x = x + 1` — that statement does not exist as a concept. If you want a "new x", you write `let x' = x + 1 in ...` or `let new_x = x + 1 in ...`
- **Shadowing:** `let x = 5 in let x = 10 in x` evaluates to 10. The inner `let` introduces a new binding named `x` that hides the outer one for the duration of its body. After the inner body completes, the outer `x` is back. This is not mutation — both bindings coexist, you just see the inner one because of scope
- **Why this is more flexible than Python variables, not less:**
  - **Equational reasoning:** if you see `let x = e1 in e2`, you can mentally substitute `x` with `e1` inside `e2` without changing meaning. In Python with mutable variables, you cannot do this — `x` might change between the assignment and the use
  - **Composability:** `let` is an expression, so you can put it inside any other expression. `1 + (let x = 5 in x * 2)` evaluates to 11. Try writing that with Python statements
  - **Refactoring safety:** moving a `let` binding around is safe because its meaning is fully determined by its scope. Moving a Python variable assignment can introduce subtle bugs because order of side effects matters
- **The Gray-Scott chain idiom:** show the actual Gray-Scott rule from `SPEC.md` section 11.5 with its 7 sequential `let` bindings. Walk through how this corresponds to the dependency graph of the Gray-Scott update equations. Note that the chain is read top-to-bottom because that's the natural reading order, but the actual computation order is decided by the interpreter. If a smart compiler wanted to reorder these for cache efficiency, it could
- **The OCaml version:** show the same chain in real OCaml. The only syntactic difference is that OCaml allows `let x = e1 in let y = e2 in body` to be written as `let x = e1 in let y = e2 in body` (same thing) or with `;;` separators in REPL contexts. Swarmlet uses the explicit `let ... in ...` everywhere
- **The Python parallel:** show the same Gray-Scott in Python with simple variable assignments. Observe that for pure computation, Python variables behave functionally — no mutation, just sequential bindings. Conclude: Python's local variables ARE essentially `let` bindings when used without mutation. The cognitive shift is realizing that this style is the **default** in FP, not the exception
- **Pitfalls:**
  - Reading `let x = 5 in x` as "assign 5 to x, return x" — close, but the assignment has scope, not "everywhere from here on"
  - Trying to write `let x = 5; x = x + 1; x` (this is invalid syntax — there is no sequential update)
  - Confusing shadowing with mutation. They look similar but have completely different semantic implications
- **Exercises:** 4 exercises:
  1. Translate this Python function (5 lines, all assignments, no mutations) to Swarmlet using `let ... in` chains
  2. Trace through the evaluation of `let x = 1 in let y = 2 in let x = x + y in x * y` step by step. What is the final value? (answer: 6, because the inner `x` is `1+2=3` and the body is `3*2`)
  3. The forest fire `Tree` rule has a `let spark = random () < 0.00005 in ...`. Why is this `let` useful? What would the rule look like without it (with `random ()` inlined)? Why is the `let` version safer for understanding?
  4. Write a Swarmlet expression that computes the average of three field values at three offsets: `field` at (0,0), (1,0), and (0,1). Use `let` bindings to name each value before averaging

**Dependencies:** SWARMLET-006

**Expected result:**
A document that converts the `let ... in ...` confusion into competent usage. After reading, the reader should be able to write deeply nested `let` chains without mental overhead.

**Acceptance criteria:**
- [ ] File exists at `swarmlet/docs/let-expressions-vs-variables.md`
- [ ] Length 400-700 lines
- [ ] Lexical scoping, immutability, and shadowing each have a dedicated subsection
- [ ] Gray-Scott chain example is reproduced from `SPEC.md` and walked through in detail
- [ ] OCaml-bridge section shows the equivalent OCaml syntax
- [ ] Python parallel shows that local variables in Python are essentially `let` bindings used functionally
- [ ] 4 exercises with hints
- [ ] No emoji
- [ ] Cross-links to SPEC.md sections 7.5 and 11.5

---

## Phase 11 — Tier 2: Architecture

### SWARMLET-030 — Doc: how the expression evaluator works

**Description:**
Write the document that walks through the implementation of `eval_expr` in `swarmlet/eval.py` — explaining how an interpreter for a functional language is itself naturally a recursive function over an AST. This is the closest analog to `prolog-engine-explained.md` in the minilog series. After reading, the reader should understand interpreters as a category of program, not just "how this specific Swarmlet thing works".

**What needs to be done:**

Create `swarmlet/docs/expression-evaluator-explained.md` covering:

- **Opening:** the reader has either implemented or is about to implement `eval_expr`. Explain that this single function is the heart of the interpreter and the most concentrated example of FP in the project
- **What an interpreter is:** a function that takes a syntax tree and a context, and returns a value. That's it. The whole field of programming language implementation is variations on this theme
- **The shape of `eval_expr`:** it dispatches on the type of AST node. For each node type, it computes the value of that node, possibly by recursively evaluating sub-nodes. Show the function signature and the dispatch structure (a big `match` or if-elif on node type)
- **Walking through each case:**
  - `Num` and `Bool`: trivial, return the literal value
  - `Var`: look up the name in the context (locals → params → builtins → state symbols → error). Discuss the lookup chain and why it has this order
  - `BinOp`: recursively evaluate left and right, apply the operator. Discuss type coercion and runtime type errors
  - `Call`: look up the builtin, recursively evaluate the arguments, call the builtin function with the values
  - `If`: recursively evaluate the condition, then **recursively evaluate only the chosen branch**. Discuss why this is "lazy in branches" — you don't evaluate the unchosen branch, which means side effects in the unchosen branch don't happen. This is different from how arguments work (they're always evaluated before the call)
  - `Let`: recursively evaluate `e1`, extend `locals` with the new binding (immutable extension — a new dict, not a mutation), recursively evaluate `e2` in the extended context. Discuss how immutability of `locals` makes scoping work correctly without explicit save/restore
  - `Match`: walk through the case-by-case algorithm in detail (try pattern, check guard, evaluate body, fall through to next case, error if none match)
- **The `EvalContext` as immutable bag:** explain why `EvalContext` is a dataclass and why every recursive call creates a new context (or reuses the same one if nothing changed). Show that this is exactly the pattern from minilog's `Substitution` — both are immutable environment-like values that thread through the evaluator
- **The recursion structure as tree traversal:** the AST is a tree, and `eval_expr` is a depth-first traversal that returns values up the tree. Each node's value is computed from its children's values. This is a fold over the AST. Mention that in real ML/Haskell, you can write this as a literal `fold` operation
- **Why interpreters are written this way in FP:** because pattern matching on AST nodes makes case dispatch trivial. Because immutable contexts make scoping bug-free. Because recursive functions naturally express tree traversal without auxiliary data structures
- **The OCaml-bridge:** show what this same evaluator would look like in real OCaml, with proper ADTs for the AST and exhaustive pattern matching:
  ```ocaml
  type expr =
    | Num of float
    | Var of string
    | If of expr * expr * expr
    | Let of string * expr * expr
    | Match of expr * (pattern * expr) list
    (* ... *)

  let rec eval_expr ctx = function
    | Num n -> VNum n
    | Var name -> lookup ctx name
    | If (cond, then_branch, else_branch) ->
        (match eval_expr ctx cond with
         | VBool true -> eval_expr ctx then_branch
         | VBool false -> eval_expr ctx else_branch
         | _ -> failwith "type error: condition must be bool")
    | Let (name, e1, body) ->
        let v = eval_expr ctx e1 in
        eval_expr (extend ctx name v) body
    | Match (scrut, cases) -> eval_match ctx (eval_expr ctx scrut) cases
    (* ... *)
  ```
  Note how the OCaml version uses real ADTs and exhaustive pattern matching — the compiler refuses to compile if you forgot a case
- **Comparison with the Python implementation:** in Python you use `isinstance` checks or `match` (3.10+) or class dispatch. In OCaml you get this for free via ADTs. Swarmlet uses Python dataclasses + isinstance checks (or `match` if Python 3.10+) — a reasonable approximation of ADTs
- **Common pitfalls:**
  - Forgetting to use `ctx.locals` extended with the new binding for the `let` body — instead mutating the original `locals` dict. This breaks scoping
  - Evaluating both branches of `if` (e.g. computing both eagerly and then choosing) — this changes semantics if branches have side effects
  - Returning a Python `int` for `Num` instead of a tagged `Value` — leads to type confusion later
- **Exercises:** 4 exercises:
  1. Trace `eval_expr` for `let x = 5 in x + 3` step by step, showing the context at each call
  2. Add a hypothetical `Squared` node type (squares its argument) to the AST. What changes are needed in `eval_expr`? How many lines?
  3. Why does `If` evaluate only the chosen branch, but `BinOp` evaluates both arguments? Construct an example where this matters
  4. The current `eval_expr` would have N levels of recursion for a `let ... in let ... in ...` chain of length N. Could this overflow Python's stack? At what N? What's the workaround in real ML languages? (Answer: tail call optimization, which Python lacks)

**Dependencies:** SWARMLET-011 (the evaluator must be implemented for the document to walk through real code)

**Expected result:**
A document that explains how interpreters work as a category of program, using the Swarmlet evaluator as the running example. After reading, the reader should be able to add a new expression form to the language by themselves.

**Acceptance criteria:**
- [ ] File exists at `swarmlet/docs/expression-evaluator-explained.md`
- [ ] Length 400-700 lines
- [ ] Every expression node type from `SPEC.md` section 4 has a walkthrough in the document
- [ ] OCaml-bridge section shows a parallel OCaml evaluator with real ADTs
- [ ] At least one full trace of an evaluation (showing context state at each step)
- [ ] 4 exercises
- [ ] No emoji
- [ ] Cross-link to SWARMLET-011 source code (will be valid after that issue closes)

---

### SWARMLET-031 — Doc: tick as a snapshot transformation

**Description:**
Write the document that explains the most beautiful idea in Swarmlet: a tick is a pure function from `snapshot` to `snapshot`. The two-phase tick is the composition of two such functions. This document covers why this design makes the engine deterministic by construction, trivially testable, and naturally parallelizable.

**What needs to be done:**

Create `swarmlet/docs/tick-as-snapshot-transformation.md` covering:

- **Opening:** the reader has implemented or is about to implement `World.step()`. Tell them they're about to write the prettiest function in the project, and they should appreciate why
- **The conceptual shift:** in imperative CA, a tick is a procedure: "go through the grid, update each cell". In functional CA, a tick is a function: "given the current snapshot, return the next snapshot". These sound equivalent but they're not — the second formulation has properties the first does not
- **What a snapshot is:** an immutable value containing all the state of the world at one moment. In Swarmlet: a numpy array of cell states, a dict of float arrays for fields, a list of agent records. None of these reference any external state. Two snapshots can coexist without interfering. A snapshot can be hashed, serialized, compared, archived
- **The cell phase as a pure function:** `cell_phase: snapshot -> snapshot`. It reads from the input, builds a fresh output, returns the output. The input is never mutated. Show the signature and the high-level pseudocode
- **The agent phase as a pure function:** same shape, but more interesting. Agents read from the post-cell-phase snapshot, produce intents, and the engine atomically applies all intents to produce a new snapshot. Discuss why the intent-collection design (separate document SWARMLET-032 covers this in detail) preserves purity
- **A tick as composition:** `step = agent_phase ∘ cell_phase`. The full tick is the composition of two pure functions. In FP, function composition is a fundamental operation, and this design reflects it explicitly
- **Why this matters #1: determinism.** Given the same input snapshot and the same RNG state, the output snapshot is always the same. There is no hidden state, no race condition, no order dependency. The determinism property in `SPEC.md` section 2.4 follows directly from the purity of the tick function
- **Why this matters #2: testing.** A test for `cell_phase` looks like: build a small input snapshot by hand, call the function, compare the output to a hand-computed expected snapshot. No mocks, no setup, no teardown, no hidden interactions. Contrast with imperative CA, where you'd need to set up a global grid object, run the procedure, then inspect the global grid afterwards
- **Why this matters #3: parallelization.** Each cell's new state depends only on the input snapshot, not on any other cell's new state. So all cells can be computed in parallel without locks. The interpreter doesn't do this in v0.1 (it iterates serially), but a v0.2 interpreter could call `numpy` vectorized operations or split the grid across CPU cores trivially
- **Why this matters #4: time travel debugging.** Because every snapshot is a value, you can save them. Save snapshot at tick 100 and tick 200, then try different rule sets starting from each. Compare diffs between consecutive snapshots. Replay a run with a different RNG seed. None of this requires special infrastructure — it falls out of the design
- **The OCaml-bridge:** show what `step` would look like in OCaml with proper functional types:
  ```ocaml
  type snapshot = {
    states: state array array;
    fields: (string * float array array) list;
    agents: agent list;
    t: int;
  }

  let cell_phase (snap: snapshot) : snapshot =
    let new_states = Array.map (fun row -> Array.map ...) snap.states in
    let new_fields = List.map (fun (name, arr) -> ...) snap.fields in
    { snap with states = new_states; fields = new_fields }

  let agent_phase (snap: snapshot) (rng: Random.State.t) : snapshot = ...

  let step (snap: snapshot) (rng: Random.State.t) : snapshot =
    snap |> cell_phase |> agent_phase rng
  ```
  Note the `|>` pipeline operator — this is OCaml's function composition syntax, and it makes the "pipe through transformations" intent explicit
- **The contrast with imperative CA:** show the same tick in imperative Python, with `self.grid` mutation and order-dependent loops. Highlight the lurking bugs (in-place writes, race in time, etc.) that simply cannot exist in the functional version
- **The minor cheat:** `World.step()` does mutate `self.t` and `self.states` (replaces with new array). Strictly speaking, `World` is not pure — it's an object with mutable state. But the **logic** of the tick (the part that decides what the new state should be) is pure. The mutation is confined to one line: `self.states = new_states`. This separation between "compute the new state purely" and "swap the new state in" is the standard FP technique for working in mutable host languages
- **Common pitfalls:**
  - Reading from `self.states` (the mutable field) inside the cell rule body, instead of from the snapshot parameter — this can break determinism if the rule is also writing to `self.states`
  - Assuming cell iteration order matters (it doesn't, by design)
  - Trying to "optimize" by mutating cells in place — this defeats the entire purpose
- **Exercises:** 4 exercises:
  1. The cell phase iterates over all cells. If you wanted to parallelize this with `multiprocessing`, what would you need to ensure? (Answer: nothing — the design already supports it. You just need to split the cell list and merge results)
  2. Sketch a "time travel debugger" for Swarmlet: given a list of snapshots from a run, what API would let a user step forward and backward through ticks? Why is this trivial in Swarmlet but hard in imperative CA?
  3. The Python implementation actually has `World.t += 1` mutating `self.t`. Is `World.step()` a pure function of `(snapshot, rng_state)` to `(snapshot, rng_state)`? Discuss
  4. If you wanted to run two parallel "branches" of the same simulation from a snapshot at tick 100 (one with feed=0.055, one with feed=0.060), how would you do this? What does this tell you about the design?

**Dependencies:** SWARMLET-016, SWARMLET-017 (both phases must be implemented to walk through real code)

**Expected result:**
A document that makes the reader feel the elegance of the snapshot-transformation design and recognize it as a general FP architectural pattern, not just "how Swarmlet happens to work".

**Acceptance criteria:**
- [ ] File exists at `swarmlet/docs/tick-as-snapshot-transformation.md`
- [ ] Length 400-700 lines
- [ ] Both phases are explained as pure functions with their signatures
- [ ] All four "why this matters" sections are present (determinism, testing, parallelization, time travel)
- [ ] OCaml-bridge with `|>` pipeline syntax is shown
- [ ] Imperative Python contrast is shown
- [ ] The "minor cheat" about `World.step()` mutation is honestly addressed
- [ ] 4 exercises
- [ ] No emoji
- [ ] Cross-links to SPEC.md section 2 and SWARMLET-016, 017

---

### SWARMLET-032 — Doc: the intent pattern

**Description:**
Write the document that explains why agent actions produce immutable `Intent` records instead of executing side effects directly. This is a non-obvious design pattern that the reader has not seen in classical OOP code, but it's everywhere in functional architectures: redux actions, database transactions, event sourcing, command pattern. Show how it preserves purity, enables conflict resolution, and makes the agent phase deterministic.

**What needs to be done:**

Create `swarmlet/docs/intent-pattern-explained.md` covering:

- **Opening:** the reader has seen `Intent` in the spec and the eval_action code. Tell them this small dataclass embodies one of the most important FP architectural patterns, and they're about to learn it through implementation
- **The naive design (what we are NOT doing):** when an agent says `move forward`, the engine could just update the agent's position immediately. When it says `kill Sheep`, the engine could just remove a sheep from the agent list. This is what an imperative CA would do
- **Why the naive design fails:** with multiple agents, you immediately hit conflicts:
  - Two agents try to move into the same cell. Who gets it?
  - Two wolves try to kill the same sheep. Who gets the kill, who gets the energy?
  - One agent's death affects another agent's read in the same tick. What does the second agent see?
  - The order of agent processing affects the result. Different runs with the same seed would produce different outcomes if the iteration order changed
- **The intent pattern in one sentence:** instead of executing the action, **describe** what the action would do, collect all descriptions across all agents, then **apply them atomically** with a defined conflict-resolution strategy
- **Walking through the `Intent` dataclass:** show the fields from SWARMLET-015. Each field corresponds to one kind of action: `move_dir`, `agent_field_writes`, `cell_field_deposits`, `spawn_types`, `kill_targets`, `die`. Note that an Intent is an **immutable record describing a desire**, not an active operation
- **The two-stage process:**
  1. **Build phase.** For each agent, evaluate the rule body, building up an Intent. The rule body is pure: it reads from the snapshot and writes to the Intent (which is local to that agent's evaluation)
  2. **Apply phase.** After all Intents are collected, the engine applies them in a defined order (movements first, with conflict resolution; then field writes; then kills; then spawns; then deaths). The order is documented in `SPEC.md` section 2.3
- **Why this preserves purity:** the rule body is a function that takes (agent, snapshot) and returns an Intent. It does not mutate anything outside its local Intent. It does not see other agents' decisions. It is testable in isolation. This is exactly the same shape as the cell rule in the previous document
- **Why this enables conflict resolution:** because intents are collected before any are applied, the engine has full visibility of all conflicts. Movement to the same cell? Pick one, the rest stay. Two kills targeting the same sheep? Pick one. The engine applies a deterministic, seeded random tiebreak — and because all the inputs are visible at apply time, the same seed produces the same resolution every time
- **Why this enables determinism:** without the intent pattern, the result of the agent phase would depend on the order in which agents were processed. With it, all agents process against the same input snapshot, and the apply phase is deterministic given the seed. Order-of-iteration becomes irrelevant for everything except the random shuffle (which is itself seeded)
- **The well-known parallels:** name the pattern in other contexts where the reader might have seen it:
  - **Redux actions** (in JavaScript frontend): components dispatch action objects, a reducer applies them to compute new state. Same shape
  - **Database transactions:** queries declare what they want to do, the database commits them atomically with conflict detection. Same shape
  - **Event sourcing:** systems log immutable events, then derive current state by replaying events. Same shape
  - **Command pattern (GoF):** encapsulate an operation as an object, dispatch later. Same shape
  - **CRDT operations:** concurrent edits are described as operations and merged by deterministic rules. Same shape
  All of these are variations of the same idea: separate "decide what to do" from "do it", with the intent in between as a value
- **The OCaml-bridge:** show what `Intent` would look like in real OCaml as a record type:
  ```ocaml
  type intent = {
    agent_id: int;
    move_dir: direction option;
    agent_field_writes: (string * value) list;
    cell_field_deposits: (string * float) list;
    spawn_types: string list;
    kill_targets: string list;
    die: bool;
  }

  let empty_intent agent_id = {
    agent_id;
    move_dir = None;
    agent_field_writes = [];
    cell_field_deposits = [];
    spawn_types = [];
    kill_targets = [];
    die = false;
  }

  let rec eval_action ctx intent = function
    | Stay -> intent
    | Die -> { intent with die = true }
    | Move expr ->
        let dir = eval_expr ctx expr in
        { intent with move_dir = Some dir }
    | Set (name, expr) ->
        let v = eval_expr ctx expr in
        if is_cell_field name then
          { intent with cell_field_deposits = (name, v) :: intent.cell_field_deposits }
        else
          { intent with agent_field_writes = (name, v) :: intent.agent_field_writes }
    | Seq actions -> List.fold_left (eval_action ctx) intent actions
    (* ... *)
  ```
  Note that in OCaml, every action returns a **new** intent (the `with` syntax creates a copy with one field changed). This is the canonical functional update pattern. The Python version mutates the intent in place for simplicity, but conceptually it's the same — it's a local mutation that only affects this agent's intent
- **The within-action visibility detail:** the spec says that within one agent's `seq` block, agent-field writes are visible to subsequent reads. Explain why this matters (for the Boids `move forward` after `set heading`) and why it's a **deliberate exception** to the "intent is fully built before anything happens" rule. The Boids alignment rule reads `self.heading` after writing it. To make this work, the agent uses a copy-on-write view of itself within the action evaluation. The persistent intent record is updated, but the `AgentView` also reflects the changes for subsequent reads. Cell-field writes do NOT have this property — they only apply at the end
- **Common pitfalls:**
  - Trying to read `cell_field` and see an updated value within the same action — it will show the pre-tick value. This is documented and intentional
  - Trying to make one agent's action affect another agent during the build phase — not possible by design
  - Writing rules that depend on the iteration order — not possible because the order is shuffled with a seeded RNG, but rules see only the snapshot, not the order
- **Exercises:** 4 exercises:
  1. Two wolves are on the same cell with one sheep. Both wolves' rules contain `kill Sheep; set energy = self.energy + 8`. Trace through what happens. Which wolf gets the kill? What is each wolf's energy after the tick? (Answer: one wolf gets the kill via random tiebreak; both wolves gain +8 energy because the gain was computed during build phase before the kill was applied — this is the documented quirk)
  2. Why can't an agent's action contain `become Grass` to change its current cell's state? (Answer: by design — cell state mutations are reserved for cell rules, not agent actions, to keep the two-phase model clean. Allowing it would require adding "agent-driven cell intents" as another category, complicating apply-order rules)
  3. Sketch how you'd extend the intent pattern to support an agent action `transfer_to other_agent N` that moves N energy from self to another agent. What new fields does Intent need? What conflict resolution issues arise?
  4. The intent pattern is essentially a small free monad over actions. Without using that terminology, explain in plain words what makes this design "compositional" — why can a `seq { a; b; c }` be safely refactored into `seq { a; b }; c` outside or `seq { a; seq { b; c } }`?

**Dependencies:** SWARMLET-015 (action evaluator implementation provides the real Intent dataclass and eval_action function to walk through)

**Expected result:**
A document that names and explains one of the most important architectural patterns in FP, so the reader recognizes it next time they see it elsewhere (redux, transactions, event sourcing).

**Acceptance criteria:**
- [ ] File exists at `swarmlet/docs/intent-pattern-explained.md`
- [ ] Length 400-700 lines
- [ ] All Intent fields are explained
- [ ] The two-stage build/apply process is diagrammed or explained step by step
- [ ] At least 5 well-known parallel patterns are named (redux, transactions, event sourcing, command, CRDT)
- [ ] OCaml-bridge with record syntax and `with` updates is shown
- [ ] The within-action visibility rule and the documented kill quirk are honestly addressed
- [ ] 4 exercises
- [ ] No emoji
- [ ] Cross-links to SPEC.md sections 2.3, 7.3 and SWARMLET-015

---

## Phase 11 — Tier 3: Deeper

### SWARMLET-033 — Doc: recursion vs iteration

**Description:**
Write the document that explains recursion as the primary control structure in FP. Show how the AST traversal in `eval_expr` is naturally recursive. Discuss tail recursion (and why Python lacks it). Compare recursion with iteration on classic problems. Introduce map/filter/fold as recursion patterns wrapped in friendly names.

**What needs to be done:**

Create `swarmlet/docs/recursion-vs-iteration.md` covering:

- **Opening:** the reader has now implemented a working interpreter. Point out that the interpreter is full of recursive functions (`eval_expr`, neighborhood iteration, AST construction in the parser). This document explains why and when to reach for recursion vs iteration
- **The mental shift:** loops are about "do this N times" — iteration is fundamentally about repetition over time. Recursion is about "this thing is built from smaller versions of the same thing" — recursion is about structural decomposition. Different problems suit different shapes
- **Classical example: sum a list.** Show iterative Python version (with accumulator), recursive Python version (`sum_list([]) = 0; sum_list([h, *t]) = h + sum_list(t)`), and OCaml version. Discuss what each version says about the data:
  - The iterative version says "I'm going to walk through and accumulate"
  - The recursive version says "the sum of a list is the head plus the sum of the tail"
- **Recursion in the Swarmlet evaluator:** `eval_expr` is recursive because the AST is recursive (an expression contains sub-expressions). Show the recursive case for `BinOp`: `eval_expr(BinOp(op, l, r)) = apply_op(op, eval_expr(l), eval_expr(r))`. The recursion mirrors the structure of the data
- **Tree traversal as recursion:** show how the parser's recursive descent and the evaluator's tree walk are both instances of "fold over a tree". Mention that in real ML/Haskell, you can write a generic `fold_expr` once and parameterize it by what to do at each node — this is called the catamorphism, and it's a common pattern
- **Tail recursion explained:** when a recursive call is the **last** thing a function does, it's a tail call. A smart compiler can replace tail calls with a jump (no stack frame growth). This makes recursion as fast as iteration. OCaml does this. Haskell does this. Lisp does this. **Python does not.** Show an example:
  ```ocaml
  let rec sum_list_tail acc = function
    | [] -> acc
    | h :: t -> sum_list_tail (acc + h) t  (* tail call *)

  let sum lst = sum_list_tail 0 lst
  ```
  vs the non-tail version which would blow the stack on long lists
- **Why Python lacks TCO:** Guido decided against it for traceback clarity. This means deeply recursive Python code can hit `RecursionError` around N=1000. In practice, this means: in Python you write deeply recursive things only when the recursion depth is bounded by the data structure size (a tree of depth 30 is fine, a list of length 10000 is not)
- **Implications for the Swarmlet evaluator:** the AST depth for any reasonable Swarmlet program is small (10-20 levels at most). So the recursive `eval_expr` is safe. But if Swarmlet allowed user-defined recursive functions, you'd hit limits quickly. This is one reason v0.1 doesn't have user-defined functions — the interpreter would need to handle recursion limits
- **Map, filter, fold as recursion patterns:** these higher-order functions are recursion with a name. `map f [a, b, c] = [f(a), f(b), f(c)]` — that's a fold that applies `f` to each element. `filter p lst` keeps elements where `p` is true. `fold f init lst` reduces the list to a single value. Show OCaml versions:
  ```ocaml
  let rec map f = function
    | [] -> []
    | h :: t -> f h :: map f t

  let rec fold f acc = function
    | [] -> acc
    | h :: t -> fold f (f acc h) t
  ```
  Note that `fold` is tail-recursive, `map` is not (the cons happens after the recursive call). Real OCaml `List.map` is implemented carefully to be efficient
- **When to use recursion vs iteration in Python:**
  - Use recursion when the data structure is recursive (tree, AST, JSON document)
  - Use iteration (`for` loop) when you're processing a flat sequence and need clear performance
  - Use list comprehensions / generators / `map` / `filter` when you're transforming a sequence — they're more functional than `for` loops and often clearer
- **The Python parallel:** show that Python list comprehensions are fold-like:
  ```python
  result = [f(x) for x in lst if p(x)]
  ```
  is the same as
  ```python
  result = list(map(f, filter(p, lst)))
  ```
  is the same as a fold:
  ```python
  result = []
  for x in lst:
      if p(x):
          result.append(f(x))
  ```
  All three express the same computation. The first is most idiomatic Python. The second is most functional. The third is most imperative. Choose by audience and clarity, not by ideology
- **Common pitfalls:**
  - Writing recursive Python on long sequences and hitting `RecursionError`
  - Forgetting that recursive solutions in Python are usually **slower** than iterative ones because of function call overhead
  - Using recursion when iteration is clearer (e.g., for a simple counter loop)
  - Not understanding why `sum_list_tail` is tail-recursive but `sum_list` is not
- **Exercises:** 4 exercises:
  1. Write a recursive function (in pseudocode) that computes the depth of a Swarmlet AST node. Hint: the depth of an `Atom` is 1; the depth of a `BinOp(_, l, r)` is `1 + max(depth(l), depth(r))`
  2. Convert this recursive `factorial` into a tail-recursive version using an accumulator
  3. Express "sum of squares of even numbers in a list" as: (a) a Python `for` loop, (b) a list comprehension, (c) a `map`+`filter`+`sum` chain, (d) a `fold` (right-fold or left-fold in pseudocode)
  4. The Swarmlet `eval_expr` is recursive. If you wanted to make it iterative (using an explicit stack), how would you do it? When would this be necessary?

**Dependencies:** SWARMLET-024 (the reader should have a working interpreter to point at as the running example)

**Expected result:**
A document that demystifies recursion and connects it to the higher-order functions every modern programmer has used (map, filter, comprehensions). After reading, the reader should be comfortable writing tail-recursive helpers and recognizing when recursion is the right tool.

**Acceptance criteria:**
- [ ] File exists at `swarmlet/docs/recursion-vs-iteration.md`
- [ ] Length 400-700 lines
- [ ] Tail recursion is explained with a concrete example
- [ ] OCaml-bridge shows tail-recursive sum and proper map/fold definitions
- [ ] Python parallel shows list comprehensions as fold-like
- [ ] Why Python lacks TCO is honestly addressed
- [ ] Connection to the Swarmlet `eval_expr` is explicit
- [ ] 4 exercises
- [ ] No emoji

---

### SWARMLET-034 — Doc: purity and side effects

**Description:**
Write the document that defines "pure function" precisely, identifies which parts of Swarmlet are pure and which are not, and explains how to control side effects (RNG, mutation, I/O) without giving up the benefits of purity. Discuss the test of purity ("can I replace a call with its return value without changing meaning?") and apply it to real Swarmlet code.

**What needs to be done:**

Create `swarmlet/docs/purity-and-side-effects.md` covering:

- **Opening:** the word "pure" gets thrown around in FP discussions like a religious term. This document defines it precisely and shows where the line is in real Swarmlet code. The reader should walk away knowing exactly which functions are pure and why
- **The definition of pure function:**
  1. Same input → same output (no dependence on hidden state)
  2. No side effects (does not modify anything outside its return value)
  These two conditions together mean: a pure function call can be replaced by its return value anywhere it appears, without changing the meaning of the program. This is called **referential transparency**, and it is the operational definition of purity
- **Examples of pure functions:** `add(a, b) = a + b`. `sqrt(x)`. `eval_expr(node, ctx)` (when ctx is immutable). Any function that takes only immutable values and returns a value
- **Examples of impure functions:** `random()` (depends on hidden RNG state). `print(x)` (modifies stdout). `os.path.exists(path)` (depends on filesystem). `time.time()` (depends on the clock). Any function that reads or writes the world outside its arguments
- **The test of purity in practice:** for each suspect function, ask: "If I call it twice with the same arguments, do I get the same result?" If yes, it's probably pure. If no, it's impure. Then ask: "If I call it once, save the result, and call it again, can I delete the second call?" If yes, the function has no side effects
- **Walking through Swarmlet:** classify each module:
  - **Pure:**
    - `eval_expr` and most of `eval.py` (when `EvalContext` is treated as immutable)
    - `parser.py` (parses a string to an AST, no side effects)
    - `analyzer.py` (walks an AST, returns errors, no side effects)
    - `lexer.py` (tokenizes a string)
    - All built-ins except `random()`, `random_int(n)`, and `random_dir()`
  - **Impure but controlled:**
    - `random()` and friends — they depend on the seeded RNG state in the context. Pure given the RNG state as part of the input. The seeded design makes the impurity reproducible
    - `World.step()` — mutates `self.t`, `self.states`, etc. Impure as a method on `World`. But the **logic** inside is pure: it's "compute new state from old state" plus a single mutation at the end
  - **Genuinely impure:**
    - `cli.py` — reads files, writes files, prints to stdout
    - `snapshot.py` `write_jsonl` and `write_npz` — write to disk
- **The principle: push impurity to the edges.** Most of Swarmlet is pure logic. The impurity is concentrated in `cli.py` and the file writers — the boundary between the program and the outside world. This is a deliberate architectural choice, and it's the standard FP advice: **"functional core, imperative shell"**. Coined by Gary Bernhardt, used everywhere in modern FP-influenced architectures
- **Why this matters:**
  - **Testing:** pure functions are trivial to test. You don't need mocks. You don't need to set up a database. You just call the function with inputs and assert on outputs
  - **Reasoning:** pure functions can be understood in isolation. You don't need to mentally simulate the rest of the program to know what they do
  - **Refactoring:** pure functions can be moved, renamed, inlined, extracted without breaking anything. Their behavior is fully determined by their signature
  - **Memoization:** pure functions can be cached. Call once, save the result, return it next time. Impure functions cannot
  - **Parallelization:** pure functions can be called from multiple threads without locks. They have no shared state to corrupt
- **Controlled impurity: the seeded RNG pattern:** show how Swarmlet handles randomness. The RNG is part of the `EvalContext`. Functions that need randomness call `ctx.rng.random()`. The RNG is initialized from a seed at `World` construction. Same seed → same sequence → same simulation. The impurity is technically there, but it's **reproducible** and **isolated**, which is enough for all practical purposes (testing, debugging, replay)
- **Common pitfalls:**
  - Calling `random.random()` from the global Python `random` module instead of `ctx.rng` — breaks determinism
  - Using `time.time()` for any reason inside a rule — breaks reproducibility
  - Reading from a file inside a built-in — breaks purity in a way that's hard to test
  - Mutating an "immutable" data structure because Python doesn't enforce immutability — accidental sharing of state across calls
- **The OCaml-bridge:** real OCaml does NOT enforce purity by default — it's a "mostly functional" language, you can use mutable references and arrays freely. Haskell goes further and uses the type system to track effects (the `IO` monad). Show a tiny example of how Haskell makes impurity visible in types:
  ```haskell
  -- pure
  add :: Int -> Int -> Int
  add x y = x + y

  -- impure: the type says "this returns an Int but does IO"
  getRandomInt :: IO Int
  getRandomInt = randomRIO (1, 100)
  ```
  Then explain that Swarmlet is closer to OCaml's "pure by convention" stance than Haskell's "pure by type system" stance. We use Python conventions (immutable dataclasses, no global state) to enforce purity socially, not technically
- **Exercises:** 4 exercises:
  1. Look at the function `World.snapshot()`. Is it pure? Why or why not?
  2. The `random_dir()` built-in: classify it as pure, controlled-impure, or genuinely-impure. Justify
  3. Suppose you wanted to add a built-in `current_tick()` that returns `World.t`. Would this be pure? Would it be a good idea? What would be a more functional alternative?
  4. A user wants to add logging inside a rule body: `log "Tree caught fire"`. Discuss how to support this without breaking the purity of rule evaluation. Hint: think of logs as another kind of intent

**Dependencies:** SWARMLET-024

**Expected result:**
A document that converts "purity" from a fuzzy moral term into a precise technical concept the reader can apply. After reading, the reader should be able to look at any Python function and classify it as pure, controlled-impure, or genuinely impure.

**Acceptance criteria:**
- [ ] File exists at `swarmlet/docs/purity-and-side-effects.md`
- [ ] Length 400-700 lines
- [ ] Definition of pure function with both conditions clearly stated
- [ ] Classification of every Swarmlet module as pure / controlled-impure / impure
- [ ] "Functional core, imperative shell" principle is named and attributed
- [ ] Seeded RNG pattern is explained
- [ ] OCaml/Haskell bridge shows the spectrum from convention to type-enforced purity
- [ ] 4 exercises
- [ ] No emoji

---

### SWARMLET-035 — Doc: algebraic data types and tagged unions

**Description:**
Write the document that explains why ML languages have AST nodes as ADTs (algebraic data types / tagged unions / sum types) and how this combines with pattern matching to make compiler/interpreter code uniquely elegant. Show what Python approximates this with (dataclass + isinstance or `match`), what real OCaml gives you (compile-time exhaustiveness, type safety), and why this is the killer combination that makes ML languages so good for language tooling.

**What needs to be done:**

Create `swarmlet/docs/algebraic-data-types.md` covering:

- **Opening:** the reader has implemented the AST in `swarmlet/ast.py` as a bunch of dataclasses, and a parser that constructs them, and an evaluator that pattern-matches on them. This document explains why this combination is the most powerful design pattern in language tooling, and why ML languages were built for exactly this kind of code
- **Two kinds of compound types:** product types (a struct with N fields, "this AND that AND that") and sum types (one of N variants, "this OR that OR that"). Most languages have product types (classes, structs, records). Few mainstream languages have sum types as a first-class concept. Sum types are what Swarmlet uses for AST nodes
- **The classical sum type example:** an expression is one of: a number, a variable, a binary operation, an if-then-else, a let, a match. That's 6 alternatives. Each alternative has its own fields. They're all "expressions", but they're structurally different
- **How Python represents this:** with a class hierarchy (subclasses of `Expr`) or with dataclasses + a tag field, or with dataclasses + isinstance checks, or with Python 3.10 `match`. Show all four:
  ```python
  # Approach 1: class hierarchy
  class Expr: pass
  class Num(Expr):
      def __init__(self, value): self.value = value
  class BinOp(Expr):
      def __init__(self, op, left, right): ...

  # Approach 2: dataclass + tag
  @dataclass
  class Expr:
      kind: str
      data: Any

  # Approach 3: separate dataclasses + isinstance
  @dataclass
  class Num: value: float
  @dataclass
  class BinOp: op: str; left: Any; right: Any
  # ... and isinstance dispatch:
  if isinstance(node, Num): ...
  elif isinstance(node, BinOp): ...

  # Approach 4: Python 3.10 match
  match node:
      case Num(value=v): ...
      case BinOp(op=o, left=l, right=r): ...
  ```
  Note that approach 3 is what Swarmlet uses (separate dataclasses, isinstance or `match` for dispatch). It's the closest Python gets to ADTs
- **How OCaml represents this:** with a single `type` declaration that lists all variants. Show the canonical AST type:
  ```ocaml
  type expr =
    | Num of float
    | Bool of bool
    | Var of string
    | BinOp of string * expr * expr
    | UnOp of string * expr
    | If of expr * expr * expr
    | Let of string * expr * expr
    | Match of expr * (pattern * expr) list

  and pattern =
    | PWildcard
    | PNum of float
    | PBool of bool
    | PIdent of string
  ```
  This is one declaration, six lines for the variants, and OCaml automatically generates: constructors, pattern matching, exhaustiveness checking, type safety. You cannot construct an invalid `expr`. You cannot forget a case in a `match`
- **The killer property: exhaustiveness checking.** When you write a `match` on an `expr` in OCaml and forget the `Var` case, the compiler refuses to compile your code with the warning "this pattern matching is not exhaustive: Var is not handled". You cannot ship code with missing cases. **This is the single most important feature for writing compilers and interpreters**, and it's why ML languages dominate that domain (OCaml, Haskell, F#, Rust, Scala — all have exhaustive ADT pattern matching)
- **Why Python can't do this well:** Python has no compile-time type checking by default. You can use `mypy` for some of it, but `mypy` does not enforce exhaustiveness on `isinstance` chains or `match` statements unless you use `assert_never` patterns and discriminated unions explicitly. The result: in Python, "I forgot a case in my AST evaluator" is a runtime bug; in OCaml, it's a compile error
- **The Python workaround:** use `assert False, f"unhandled case: {type(node).__name__}"` at the end of every dispatch chain. Run extensive tests. Hope you covered everything. This is what Swarmlet does. It works, but it's strictly inferior to the OCaml approach
- **Product types vs sum types in the same language:** OCaml has both. Records are product types (`type point = { x: float; y: float }`), variants are sum types (`type shape = Circle of float | Square of float`). Python dataclasses are product types only — to get sum types, you compose dataclasses with isinstance dispatch. This is why Python ASTs are more verbose than OCaml ASTs
- **Why this matters for the Swarmlet learner:** when you implement the AST and the evaluator, you're writing the Python approximation of ADTs and exhaustive pattern matching. You're getting 80% of the value with 120% of the syntax. This is fine for learning — you understand the structure. When you eventually try real OCaml, the syntax suddenly becomes shorter and the compiler suddenly becomes your safety net
- **The deeper lesson:** ADTs and pattern matching are not "two features that happen to be in the same language family". They are **two halves of the same design**. ADTs let you describe a set of structurally different alternatives. Pattern matching lets you process those alternatives without any boilerplate. Together, they are the natural way to express "this can be one of several things, and I want to do something different for each". Compilers, interpreters, parsers, ASTs, JSON walkers, configuration validators — all of these are the same shape, and ADTs+pattern matching is the killer tool
- **Common pitfalls:**
  - Trying to add a new AST node type and forgetting to add a case in the evaluator — Python won't tell you, you'll find out at runtime
  - Using a Python class hierarchy with virtual methods instead of dataclasses + dispatch — works but loses the "data is just data" simplicity
  - Mixing concerns by adding methods to AST classes (`Num.evaluate(self, ctx)`) instead of having a separate `eval_expr` function — this is the OOP approach and it makes adding new operations on the AST harder, not easier (the expression problem)
- **A note on the expression problem:** mention briefly that ADTs make it easy to add new **operations** on existing types (just write a new function), but hard to add new **types** (you have to update every function). OOP is the opposite: easy to add new types, hard to add new operations. This is called the **expression problem** and is one of the deep tensions in PL design. For interpreters and compilers, you usually want the ADT side, because you have a fixed set of node types and many operations
- **Exercises:** 4 exercises:
  1. Look at `swarmlet/ast.py`. How would you add a new AST node `Pow` (power operation)? What files need to change?
  2. In OCaml, the same change would require touching: the type definition (1 line), the parser (a few lines for the new operator), the evaluator (a few lines for the new case). Estimate: how many places in the Python implementation need to change? Why is OCaml shorter?
  3. The Python `match` statement has a feature called "structural pattern matching" that's close to ADT pattern matching. Write the evaluator's `eval_expr` dispatch using Python 3.10 `match` syntax instead of `isinstance` chains. Compare readability
  4. Why is "the expression problem" called "the expression problem"? Hint: it has to do with two ways of organizing the same matrix (types × operations)

**Dependencies:** SWARMLET-024

**Expected result:**
A document that names the ADT + pattern matching combination as the killer pattern of ML languages, explains why Python approximates it imperfectly, and convinces the reader that real OCaml/Haskell/Rust would make the Swarmlet implementation half as long with twice the safety.

**Acceptance criteria:**
- [ ] File exists at `swarmlet/docs/algebraic-data-types.md`
- [ ] Length 400-700 lines
- [ ] Both kinds of compound types (product, sum) are defined
- [ ] All four Python representations are shown side by side
- [ ] OCaml ADT for the Swarmlet AST is shown
- [ ] Exhaustiveness checking is explained as the killer feature
- [ ] The expression problem is mentioned and briefly explained
- [ ] 4 exercises
- [ ] No emoji

---

## Phase 11 — Tier 4: Bridges

### SWARMLET-036 — Doc: from Swarmlet to Protelis (aggregate programming bridge)

**Description:**
Write the bridge document that connects Swarmlet (a simulation tool for cellular automata + agents on a grid) to Protelis (a real deployment language for swarm robotics built on the field calculus). After completing Swarmlet, the reader has the conceptual foundation to understand why aggregate programming is a different paradigm and where the natural progression leads. This document is the bridge from "I built a CA simulator" to "I'm ready to study Protelis for real swarm deployment".

**What needs to be done:**

Create `swarmlet/docs/from-swarmlet-to-protelis.md` covering:

- **Opening:** the reader now has a working Swarmlet, has run Boids, ant foraging, predator-prey, and Gray-Scott. They've internalized cellular automata + local agent rules + stigmergic fields. This document explains what comes next: aggregate programming, field calculus, and Protelis as the deployment-grade tool for swarm robotics
- **Recap of the Swarmlet paradigm:** local rules. Each cell or agent decides its next state based only on its local neighborhood. Global behavior emerges from local interactions. This is the **agent-based modeling** paradigm: you specify individual behavior, you run the simulation, you observe what emerges
- **The other paradigm: aggregate programming.** Instead of specifying individual behavior and observing what emerges, you specify the **desired collective behavior** and let the runtime decompose it into individual rules automatically. Example: instead of writing "each ant deposits pheromone and follows the gradient", you write "compute a field of distance from each food source, agents move down the gradient". The decomposition is the runtime's job
- **Field calculus in one sentence:** every value in your program is a **field** — a distribution of values across space and time. `temperature` is not "the temperature here"; it's "the temperature everywhere, varying across the network". Operations on fields automatically operate everywhere. This is the mathematical foundation of Protelis
- **The four primitives of field calculus:**
  1. **Constant fields:** a literal value (e.g. `0`) becomes a field that has that value everywhere
  2. **Sensor fields:** local sensor readings (e.g. temperature, location) become fields with one value per device
  3. **Neighborhood operations (`nbr`):** read the values of a field at all neighboring devices and aggregate (sum, min, max, average)
  4. **State persistence (`rep`):** carry a value from one tick to the next, like Swarmlet's cell fields
  Composing these four primitives lets you write distance gradients, consensus algorithms, leader election, gossip protocols, all as field expressions
- **Show a Protelis-style gradient algorithm:** the canonical example is computing distance from a source. In Protelis it looks roughly like:
  ```
  def gradient(source) {
    rep (d <- Infinity) {
      mux (source) { 0 } else {
        minHood(nbr(d) + nbrRange())
      }
    }
  }
  ```
  This computes, at every device, the distance to the nearest source. Each device executes the same code, but the result is a field — a value at every device. The `nbr(d)` reads the distance estimates from neighbors, `minHood` takes the minimum, `nbrRange()` is the distance to each neighbor, `rep` carries the result to the next tick
- **The same idea in Swarmlet:** show how you'd compute "distance to nearest food cell" in Swarmlet using the `distance_to` built-in (which we added inspired by Protelis):
  ```
  field food_distance = 0.0

  let cell _ = seq {
    set food_distance = distance_to Food
  }
  ```
  In Swarmlet this is one line because `distance_to` is a built-in. In Protelis, you'd implement it from primitives. Discuss the tradeoff: Swarmlet is higher-level for specific common operations; Protelis is lower-level but more composable
- **Why aggregate programming exists:** for **real distributed systems** (not simulations), you need:
  - **Resilience:** devices fail, networks drop messages, clocks drift. Algorithms must self-stabilize
  - **Scalability:** you can't centralize anything. All algorithms must be local
  - **Composability:** you want to combine "compute distance" with "find leader" with "spread data" without rewriting from scratch
  Aggregate programming addresses all three at the language level. Field calculus has been mathematically proven to be self-stabilizing for the right class of algorithms. Protelis programs **automatically work across a network of unreliable devices**, which is what you need for swarm robotics in the wild
- **The natural progression for Vitalii:** Swarmlet teaches you the conceptual building blocks (CA, fields, local rules, stigmergy) in a controlled simulation environment. Protelis (or its Scala cousin ScaFi) is the next step when you want to deploy to real hardware. The progression is:
  1. **Swarmlet** — learn local rules, CA, field operations in simulation
  2. **Read Protelis foundational papers** — "Practical Aggregate Programming" (Pianini 2015), "A Calculus of Computational Fields" (Viroli 2013)
  3. **Protelis tutorials with Alchemist simulator** — get hands-on with field calculus in their official sandbox
  4. **ScaFi or Protelis for a small real deployment** — Raspberry Pi cluster, or microcontrollers with mesh networking
  5. **Production swarm work** — drone fleets, sensor networks, your own miltech project
  Each step builds on the previous. Swarmlet is step 1 and arguably step 2 of that path. Steps 3-5 are months of work each
- **What Swarmlet does NOT teach you:** be honest about the limitations. Swarmlet does not teach:
  - Distributed consensus
  - Self-stabilization under failures
  - Time synchronization across devices
  - Network protocols (MQTT, mesh routing)
  - Real hardware constraints (battery, RF interference, sensor noise)
  - Anything about ROS, microcontrollers, or actual robotics control
  These are all addressed by other tools and require their own learning curves. Swarmlet teaches **the conceptual core** that all of them share: local rules generate global behavior. That's a non-trivial part of the picture, but it's not the whole picture
- **The connection to Vitalii's miltech goals:** explicitly say: this trajectory aligns with the long-term goal of building autonomous ground systems with swarm coordination. Swarmlet is "playground for thinking about swarm logic". Protelis is "production-grade DSL for swarm logic on real devices". ROS + flight controllers + sensor fusion is "everything below swarm logic". Your work eventually integrates all three layers; Swarmlet is the right place to start because it's pure, fast, and isolates the hardest cognitive shift (local-to-global) from all the engineering noise
- **No exercises in this document** — it's a bridge, not a tutorial. Just a reading list at the end:
  - Pianini, Beal, Viroli. "Practical Aggregate Programming with Protelis." (2015 paper)
  - Viroli, Damiani, Beal. "A Calculus of Computational Fields." (2013 foundational paper)
  - Beal, Pianini, Viroli. "Aggregate Programming for the Internet of Things." IEEE Computer 48(9), 2015
  - The Protelis website: protelis.github.io
  - The ScaFi project: scafi.github.io
  - Beal's GitHub for example projects

**Dependencies:** SWARMLET-024 (working v0.1 reference)

**Expected result:**
A bridge document that turns "I built a CA simulator" into "I know what to read next to move toward real swarm robotics". Honest about what Swarmlet teaches and what it doesn't.

**Acceptance criteria:**
- [ ] File exists at `swarmlet/docs/from-swarmlet-to-protelis.md`
- [ ] Length 400-700 lines
- [ ] Both paradigms (ABM and aggregate programming) are clearly distinguished
- [ ] Field calculus four primitives are listed
- [ ] At least one Protelis code example is shown with explanation
- [ ] The Swarmlet `distance_to` builtin is connected to its Protelis origin
- [ ] The natural progression (5 steps) is laid out
- [ ] Honest list of what Swarmlet does NOT teach
- [ ] Reading list at the end with at least 5 sources
- [ ] No exercises (it's a bridge document)
- [ ] No emoji

---

### SWARMLET-037 — Doc: Swarmlet and Codex axioms (cross-project bridge)

**Description:**
Write a short bridge document connecting the declarative style of Swarmlet to Vitalii's other declarative-rules project: minilog and Codex axioms. This is a cross-project synthesis showing that the FP intuition transfers naturally from one declarative DSL to another, and that working on multiple small DSLs in parallel reinforces both. Shorter document than the others because it's optional reading.

**What needs to be done:**

Create `swarmlet/docs/swarmlet-and-codex-axioms.md` covering:

- **Opening:** Vitalii is also working on minilog (a Prolog-like language for declarative reasoning) and on Codex axioms (a separate project that uses formal axioms to validate computations). This document is a short essay on how the conceptual machinery of Swarmlet and the conceptual machinery of those projects are siblings. Reading is optional; it's here to connect the dots if you've been working on multiple projects in parallel
- **The shared family:** all three are **declarative DSLs**. You describe what should be true (or what should happen), not how to compute it step by step. The runtime does the "how". Compare:
  - **Swarmlet:** "this cell becomes Fire if any neighbor is on fire" (declarative rule)
  - **Minilog:** "X is an ancestor of Y if X is a parent of Y, or if X is a parent of Z and Z is an ancestor of Y" (declarative Horn clause)
  - **Codex axioms:** "this cluster is coherent if its signature has no overlap with the forbidden prefix list" (declarative axiom)
- **The shared mechanics:**
  - **AST + interpreter pattern.** All three projects parse text into an AST and interpret the AST. The interpreter loop in each project is a recursive function over the AST. The same pattern, applied to different target languages
  - **Pattern matching as the core dispatch.** All three rely on matching some kind of structured value against patterns. Swarmlet matches cell states. Minilog matches term structures. Codex matches signature patterns
  - **Pure functions and immutable contexts.** All three carry an immutable context (locals, substitutions, validation state) through recursive calls. None of them mutate global state during evaluation
- **The shared pitfalls:**
  - **Determinism is sacred.** All three need reproducible runs. All three use seeded RNG or no RNG at all. All three have determinism tests
  - **Nested constructs need parentheses.** Minilog has the analog of Swarmlet's "nested match must be parenthesized" rule. Codex has analogous parenthesization rules. The reason is the same: parsing ambiguity
  - **Static vs runtime errors.** All three benefit from catching as much as possible at parse/load time, raising clear errors before any computation happens
- **The intuition transfer:** when you implement `eval_expr` in Swarmlet, you'll find yourself thinking "this is the same shape as `solve` in minilog". When you write a static analyzer for Swarmlet, you'll find yourself thinking "this is the same shape as the static checker in Codex". The patterns are universal because the underlying problem (interpret a small declarative language) is the same
- **The reverse benefit:** working on Swarmlet will make you a better minilog implementer. Working on minilog will make you a better Swarmlet implementer. Each project clarifies for the other where the boundaries are between language design, parser, evaluator, and runtime
- **A specific connection: forward chaining as cellular automaton.** Minilog has forward chaining (saturate the knowledge base by applying rules). This is conceptually equivalent to running a CA: each rule application is a cell update, the fixpoint is the steady state. Both are "iteratively apply local rules until nothing changes". The mathematical structure is the same — both are computations of a least fixed point of a monotone operator over a powerset (in CA: cell states; in logic: derived facts)
- **A specific connection: cell states as Horn clause atoms.** A cell state in Swarmlet is conceptually like a unary predicate in Horn logic. `let cell Tree = Fire when any Fire` reads as `Fire(cell) :- exists neighbor n: Fire(n)`. The rule structure is the same; the data is constrained to a 2D grid in Swarmlet but free in logic. Both are "if some condition holds, derive this new fact"
- **Why this matters for thinking, not just for coding:** parallel work on multiple small DSLs builds a meta-skill: recognizing when a problem is "really a small language" and reaching for the AST + interpreter + analyzer pattern. Once you see this, you start spotting it everywhere — configuration files, business rules, validation logic, query languages, anywhere there's a "describe what you want, the system figures out how". This meta-skill is one of the most valuable things you can take from the FP world into the imperative day job
- **No exercises** — this is a synthesis document, not a tutorial. End with a short note that the reader should keep both projects' specs open side by side when implementing similar features (e.g. when implementing the parser, comparing minilog's parser and Swarmlet's parser side by side)

**Dependencies:** SWARMLET-024, plus the existence of minilog as a sibling project (which already exists in `/Users/Vitalii_Bondarenko2/development/minilog/`)

**Expected result:**
A short essay that ties Swarmlet to the broader landscape of small declarative DSLs in Vitalii's work, encouraging cross-pollination of intuition between projects.

**Acceptance criteria:**
- [ ] File exists at `swarmlet/docs/swarmlet-and-codex-axioms.md`
- [ ] Length 200-400 lines (shorter than others — it's optional)
- [ ] Shared family identified with at least 3 examples
- [ ] Shared mechanics listed with at least 3 items
- [ ] Specific connection to forward chaining is made
- [ ] Specific connection between cell states and Horn clauses is made
- [ ] No exercises
- [ ] No emoji
- [ ] References both `/Users/Vitalii_Bondarenko2/development/minilog/` and the planned Codex axioms project

---

### SWARMLET-038 — Cheatsheet: Swarmlet syntax one-pager

**Description:**
Write a one-page (or two-page) cheatsheet covering all Swarmlet v0.1 syntax with one-line examples. Intended as a quick reference when the reader knows what they want to do but forgot the exact syntax. Faster to consult than the spec for syntactic questions.

**What needs to be done:**

Create `swarmlet/docs/swarmlet-syntax-cheatsheet.md` covering:

- **One-line description:** "Quick reference for Swarmlet v0.1 syntax. For semantics, see SPEC.md."
- **Sections, each with 1-3 line examples:**
  - **World declaration:** `world 100 x 100 wrap`, `world 50 x 50 bounded`
  - **Cell states:** `cell states Empty | Tree | Fire`
  - **Cell fields:** `field pheromone = 0.0`
  - **Parameters:** `param feed = 0.060`
  - **Agent declaration:** `agent Ant { carrying = 0, heading = 0 }`
  - **Cell rules:**
    - Single expression: `let cell Fire = Ash`
    - With if/else: `let cell Tree = if any Fire then Fire else Tree`
    - With match: `let cell Tree = match any Fire with | true -> Fire | false -> Tree`
    - With seq for fields: `let cell _ = seq { set pheromone = field pheromone * 0.98 }`
    - With become: `let cell Empty = seq { set grass_age = field grass_age + 1.0; if field grass_age > 30.0 then become Grass else stay }`
  - **Agent rules:**
    - Simple move: `let agent Ant = move forward`
    - Conditional: `let agent Ant = if cell_state == Food then set carrying = 1 else stay`
    - Sequential actions: `let agent Ant = seq { set energy = self.energy - 1; if self.energy <= 0 then die else stay }`
    - With kill: `let agent Wolf = if agents_of_type_in_radius Sheep 0 > 0 then seq { kill Sheep; set energy = self.energy + 8 } else stay`
  - **Initialization:**
    - `init cell = if random () < 0.5 then Tree else Empty`
    - `init field v = if x > 95 and x < 105 then 0.5 else 0.0`
    - `init agent Ant 200`
  - **Expressions:**
    - `let x = 5 in x * 2`
    - `if cond then a else b`
    - `match v with | A -> 1 | B | C -> 2 | _ -> 0`
    - `not (a and b) or c`
    - `(self.energy + 1) mod 8`
  - **Pattern syntax:**
    - Wildcard: `_`
    - State: `Tree`, `Fire`
    - Number: `0`, `3.14`
    - Boolean: `true`, `false`
    - Or-pattern: `Tree | Sapling`
    - With guard: `n when n > 5`
- **Built-in quick reference table** with two columns: Function | One-line description. Cover all built-ins from SPEC.md sections 6.1-6.5 in compact form
- **Direction encoding mini-table:** 0..7 directions with their (dx, dy) and the heading-relative names (forward, right, etc. for heading 0)
- **Common idioms section:** 4-5 patterns the reader will use repeatedly:
  - "Probabilistic transition": `let p = random () in if p < threshold then NewState else CurrentState`
  - "Decay a field": `set f = field f * decay_rate`
  - "Move toward a gradient": `move (argmax_neighbor field_name)`
  - "Flee from a target": `move ((nearest_agent_of_type_dir T r + 4) mod 8)`
  - "Reproduce when well-fed": `if self.energy > thresh then seq { set energy = self.energy / 2; spawn Self } else stay`

**Dependencies:** SWARMLET-024 (all syntax must be implemented)

**Expected result:**
A one-page reference that the reader will print or pin in their editor. Faster than looking up the spec for any syntactic question.

**Acceptance criteria:**
- [ ] File exists at `swarmlet/docs/swarmlet-syntax-cheatsheet.md`
- [ ] Length 100-200 lines (intentionally short — it's a reference, not a tutorial)
- [ ] Every syntactic form from SPEC.md section 4 has at least one example
- [ ] Every built-in from SPEC.md section 6 appears in the quick reference table
- [ ] Direction encoding mini-table is present
- [ ] Common idioms section has at least 4 patterns
- [ ] No prose paragraphs longer than 3 lines
- [ ] No emoji
- [ ] Renders cleanly on GitHub markdown preview

---

## Phase 11 scope notes

**Total Phase 11 effort:** 12 issues, ~9-12 days of writing time for one author working alone, or ~5-7 days if drafted by Claude Code with author review. None of the documentation issues block implementation issues — they can be written in parallel with implementation work, or in a dedicated documentation sprint after Phase 9 completes.

**Recommended workflow for the author:**

1. **Read SWARMLET-027 before starting any implementation.** This is the foundation document. Without it, the rest of the project will feel alien.
2. **For each implementation milestone, read the corresponding documents from the schedule above.** This turns the project into "concept → implement → see concept work → next concept" instead of "specification → implement → debug".
3. **After SWARMLET-024 (working v0.1), read the Tier 3 and Tier 4 documents.** These are post-completion reflections that make sense once you have a working system to point at.
4. **Keep the cheatsheet (SWARMLET-038) open in a side pane while writing Swarmlet code.** Faster than looking things up in the spec.

**Files created by Phase 11:**
- `swarmlet/docs/fp-mental-model.md`
- `swarmlet/docs/pattern-matching-explained.md`
- `swarmlet/docs/let-expressions-vs-variables.md`
- `swarmlet/docs/expression-evaluator-explained.md`
- `swarmlet/docs/tick-as-snapshot-transformation.md`
- `swarmlet/docs/intent-pattern-explained.md`
- `swarmlet/docs/recursion-vs-iteration.md`
- `swarmlet/docs/purity-and-side-effects.md`
- `swarmlet/docs/algebraic-data-types.md`
- `swarmlet/docs/from-swarmlet-to-protelis.md`
- `swarmlet/docs/swarmlet-and-codex-axioms.md`
- `swarmlet/docs/swarmlet-syntax-cheatsheet.md`

**Files NOT touched by Phase 11:** anything in `swarmlet/` package itself. Phase 11 is purely additive content. All implementation is finished by SWARMLET-024.

**Critical content gates:**

- **Style consistency.** All 12 documents must read like they were written by the same author. The reference style is `prolog-engine-explained.md` from minilog. Spot-check each new document against that file
- **Code validity.** Every Swarmlet snippet in every document must parse against the v0.1 grammar. If the implementation changes a rule, the affected documents must be updated
- **OCaml validity.** Every OCaml snippet must compile in a fresh `ocaml` REPL. Test before publishing each document
- **Cross-link integrity.** All `SPEC.md` section references must point to valid sections. All cross-document links must resolve

**Suggested batch-writing approach (if Claude Code is doing the drafting):**

1. Write SWARMLET-027 first as the style anchor. Review heavily, refine voice
2. Write SWARMLET-028 and SWARMLET-029 as the rest of Tier 1, matching the style anchor
3. Write SWARMLET-030, 031, 032 as Tier 2 batch
4. Write SWARMLET-033, 034, 035 as Tier 3 batch
5. Write SWARMLET-036, 037, 038 as Tier 4 batch
6. Final pass: cross-link integrity check, style consistency check, code validity check

**After Phase 11 is merged,** Swarmlet has not just a working interpreter but a complete educational resource that uses the project as a vehicle for learning functional programming. The reader who follows the recommended workflow gains: working Swarmlet implementation, working knowledge of FP concepts, OCaml literacy sufficient to read tutorials, and a clear next-step path toward Protelis and real swarm robotics.
