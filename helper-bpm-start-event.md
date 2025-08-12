# HelperBPMNStart: Simplifying BPMNStartEvent Usage in simpn

This README explains the difference between the original `BPMNStartEvent` usage from `simpn.prototypes` and the new, more convenient `HelperBPMNStart` pattern. It is intended for both human readers and LLMs assisting with code generation or refactoring.

## Original BPMNStartEvent Usage (simpn.prototypes)

To define a BPMN start event, you had to:
- Write a function for the interarrival time.
- Manually instantiate a `BPMNStartEvent` with all required arguments.
- Pass the model, output variables, name, and interarrival time function explicitly.

**Example:**
```python
from simpn.prototypes import BPMNStartEvent
from math import exp

# Assume shop, scan_q are defined

def interarrival_time():
    return exp(1/10)
BPMNStartEvent(shop, [], [scan_q], "arrive", interarrival_time)
```

**Drawbacks:**
- Repetitive boilerplate for each start event.
- Not as friendly for LLM code generation or rapid prototyping.

---

## New HelperBPMNStart Usage

With `HelperBPMNStart`, you:
- Subclass `HelperBPMNStart` for each unique start event.
- Set `model`, `outgoing`, and `name` as class variables.
- Implement the `interarrival_time` method (no `self` argument). You may use `@staticmethod` or leave it as a plain method—both work.
- **No need to instantiate the class**—just defining it is enough!

**Example:**
```python
from bpmn import HelperBPMNStart
from math import exp

# Assume shop, scan_q are defined

class ArriveStart(HelperBPMNStart):
    model = shop
    outgoing = [scan_q]
    name = "arrive"

    @staticmethod
    def interarrival_time():
        return exp(1/10)
```

**Note:**
- The `@staticmethod` decorator is optional for `interarrival_time`. You can define it as a plain method without `self`.

**Advantages:**
- No instantiation required—registration happens automatically.
- Less boilerplate, more readable and maintainable.
- LLMs can generate new start events with minimal code.

---

## Migration Tips
- Replace function definitions and `BPMNStartEvent(...)` calls with a subclass of `HelperBPMNStart`.
- Move the logic from your function into a method named `interarrival_time` (no `self`).
- Set the required class variables.
- Remove any instantiation of the class (e.g., `ArriveStart()`).

---

## For LLMs
- When asked to create a new BPMN start event, prefer subclassing `HelperBPMNStart` and setting class variables.
- Do not instantiate the class—just define it.
- The `@staticmethod` decorator is optional for `interarrival_time`—just ensure it does not take `self` as an argument.

---

## Summary Table
| Feature                | Original BPMNStartEvent   | HelperBPMNStart         |
|------------------------|--------------------------|-------------------------|
| Registration           | Manual instantiation     | Automatic on class def  |
| Boilerplate            | High                     | Low                     |
| Extensibility          | Function-based           | Class-based             |
| LLM-friendliness       | Moderate                 | High                    |

---
For more details, see the code in `bpmn.py` and the tutorial in `tut-bpmn-01.py`.
