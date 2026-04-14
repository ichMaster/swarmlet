# Swarmlet Quickstart

A 5-minute walkthrough from install to running your first simulation.

## 1. Install

```bash
git clone https://github.com/ichMaster/swarmlet.git
cd swarmlet
pip install -e ".[dev]"
```

Verify:

```bash
swarmlet --version
```

## 2. Run the forest fire model

```bash
swarmlet run swarmlet/examples/forest_fire.swl --ticks 100 --seed 42
```

Output:

```
Ticks: 100
Elapsed: 5.2s
```

## 3. Export to JSONL and inspect

```bash
swarmlet run swarmlet/examples/forest_fire.swl --ticks 50 --seed 42 --out /tmp/ff.jsonl
```

Inspect the first snapshot:

```bash
head -1 /tmp/ff.jsonl | python3 -m json.tool | head -20
```

Each line is a JSON object with `tick`, `states` (2D grid), `fields`, and `agents`.

## 4. Modify parameters

The forest fire model has three tunable parameters: `growth_rate`, `ignition_rate`, and `ash_clear_rate`. Override them at runtime:

```bash
swarmlet run swarmlet/examples/forest_fire.swl --ticks 100 --seed 42 \
  -p growth_rate=0.01 -p ignition_rate=0.001
```

Higher growth and ignition rates produce more dynamic behavior.

## 5. Write your own program

Create `my_model.swl`:

```
world 50 x 50 wrap
cell states Dead | Alive

let cell Dead =
  if count Alive == 3 then Alive else Dead

let cell Alive =
  let n = count Alive in
  if n < 2 or n > 3 then Dead else Alive

init cell =
  if random () < 0.3 then Alive else Dead
```

Run it:

```bash
swarmlet run my_model.swl --ticks 200 --seed 42 --out /tmp/life.jsonl
```

## 6. Use the Python API

```python
from swarmlet.parser import parse
from swarmlet.engine import World

with open("swarmlet/examples/forest_fire.swl") as f:
    prog = parse(f.read())

world = World(prog, seed=42)
world.step(100)

snap = world.snapshot()
print(f"Tick {snap['tick']}, agents: {len(snap['agents'])}")
```

## Next steps

- Read the [API reference](api.md) for full documentation
- Explore the [five reference examples](../swarmlet/examples/)
- Read the [language specification](../specification/Swarmlet-SPEC.md)
