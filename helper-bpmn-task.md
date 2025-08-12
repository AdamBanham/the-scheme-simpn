# HelperBPMNTask: Simplifying BPMNTask Usage in simpn

This README explains the difference between the original `BPMNTask` usage from `simpn.prototypes` and the new, more convenient `HelperBPMNTask` pattern. It is intended for both human readers and LLMs assisting with code generation or refactoring.

## Original BPMNTask Usage (simpn.prototypes)

To define a BPMN task, you had to:
- Write a function for the task's behavior.
- Manually instantiate a `BPMNTask` with all required arguments.
- Pass the model, input/output variables, name, and behavior function explicitly.

**Example:**
```python
from simpn.prototypes import BPMNTask
from simpn.simulator import SimToken
from math import exp

# Assume shop, scan_q, cassier, bag_q, bagger, done are defined

def scan(c, r):
    return [SimToken((c, r), delay=exp(1/9))]
BPMNTask(shop, [scan_q, cassier], [bag_q, cassier], "scan", scan)

def bag(c, r):
    return [SimToken((c, r), delay=exp(1/9))]
BPMNTask(shop, [bag_q, bagger], [done, bagger], "bag", bag)
```

**Drawbacks:**
- Repetitive boilerplate for each task.
- Harder to extend with custom guards or output behaviors.
- Not as friendly for LLM code generation or rapid prototyping.

---


## New HelperBPMNTask Usage

With `HelperBPMNTask`, you:
- Subclass `HelperBPMNTask` for each unique task.
- Set `model`, `incoming`, `outgoing`, and `name` as class variables.
- Implement the `behaviour` method (no `self` argument). You may use `@staticmethod` or leave it as a plain method—both work.
- Optionally, add `guard` and `outgoing_behaviour` as static/class methods or plain methods (no `self`).
- **No need to instantiate the class**—just defining it is enough!

**Example:**
```python
from bpmn import HelperBPMNTask
from simpn.simulator import SimToken
from math import exp

# Assume shop, scan_q, cassier, bag_q, bagger, done are defined

class ScanTask(HelperBPMNTask):
    model = shop
    incoming = [scan_q, cassier]
    outgoing = [bag_q, cassier]
    name = "scan"

    def behaviour(c, r):
        return [SimToken((c, r), delay=exp(1/9))]

class BagTask(HelperBPMNTask):
    model = shop
    incoming = [bag_q, bagger]
    outgoing = [done, bagger]
    name = "bag"

    def behaviour(c, r):
        return [SimToken((c, r), delay=exp(1/9))]
```

**Note:**
- The `@staticmethod` decorator is optional for `behaviour`, `guard`, and `outgoing_behaviour`. You can define them as plain methods without `self`.

**Advantages:**
- No instantiation required—registration happens automatically.
- Less boilerplate, more readable and maintainable.
- Easy to extend with custom guards or output behaviors.
- LLMs can generate new tasks with minimal code.

---


## Migration Tips
- Replace function definitions and `BPMNTask(...)` calls with a subclass of `HelperBPMNTask`.
- Move the logic from your function into a method named `behaviour` (no `self`).
- Set the required class variables.
- Remove any instantiation of the class (e.g., `ScanTask()`).

---


## For LLMs
- When asked to create a new BPMN task, prefer subclassing `HelperBPMNTask` and setting class variables.
- Do not instantiate the class—just define it.
- The `@staticmethod` decorator is optional for `behaviour`, `guard`, and `outgoing_behaviour`—just ensure they do not take `self` as an argument.

---

## Summary Table
| Feature                | Original BPMNTask         | HelperBPMNTask         |
|------------------------|--------------------------|------------------------|
| Registration           | Manual instantiation     | Automatic on class def |
| Boilerplate            | High                     | Low                    |
| Extensibility          | Function-based           | Class-based            |
| LLM-friendliness       | Moderate                 | High                   |
| Custom guards/outputs  | Manual                   | Easy (static methods)  |

---
For more details, see the code in `bpmn.py` and the tutorial in `tut-bpmn-01.py`.
