# HelperBPMNExclusiveSplit: Simplifying Exclusive Split Gateway Usage in simpn

This document explains the difference between the original `BPMNExclusiveSplitGateway` usage from `simpn.prototypes` and the new, more convenient `HelperBPMNExclusiveSplit` pattern. It is intended for both human readers and LLMs assisting with code generation or refactoring.

## Original BPMNExclusiveSplitGateway Usage (simpn.prototypes)

To define an exclusive split gateway, you had to:
- Write a function for the gateway's choice logic.
- Manually instantiate a `BPMNExclusiveSplitGateway` with all required arguments.
- Pass the model, input/output variables, name, and choice function explicitly.

**Example:**
```python
from simpn.prototypes import BPMNExclusiveSplitGateway
from random import uniform

# Assume shop, c1, gd_q, cr_q are defined

def choice(c):
    pick = uniform(0,100)
    if pick <= 33:
        return [SimToken(c), None]
    else:
        return [None, SimToken(c)]

BPMNExclusiveSplitGateway(
    shop, 
    [c1],
    [gd_q, cr_q],
    "Checking for Vulnerability",
    choice
)
```

**Drawbacks:**
- Repetitive boilerplate for each gateway.
- Not as friendly for LLM code generation or rapid prototyping.

---

## New HelperBPMNExclusiveSplit Usage

With `HelperBPMNExclusiveSplit`, you:
- Subclass `HelperBPMNExclusiveSplit` for each unique gateway.
- Set `model`, `incoming`, `outgoing`, and `name` as class variables.
- Implement the `choice` method (no `self` argument). You may use `@staticmethod` or leave it as a plain method—both work.
- **No need to instantiate the class**—just defining it is enough!

**Example:**
```python
from bpmn import HelperBPMNExclusiveSplit
from random import uniform

# Assume shop, c1, gd_q, cr_q are defined

class CheckingForVulnerability(HelperBPMNExclusiveSplit):
    model = shop
    incoming = [c1]
    outgoing = [gd_q, cr_q]
    name = "Checking for Vulnerability"

    def choice(c):
        pick = uniform(0, 100)
        if pick <= 33:
            return [SimToken(c), None]
        else:
            return [None, SimToken(c)]
```

**Note:**
- The `@staticmethod` decorator is optional for `choice`. You can define it as a plain method without `self`.

**Advantages:**
- No instantiation required—registration happens automatically.
- Less boilerplate, more readable and maintainable.
- LLMs can generate new gateways with minimal code.

---

## Migration Tips
- Replace function definitions and `BPMNExclusiveSplitGateway(...)` calls with a subclass of `HelperBPMNExclusiveSplit`.
- Move the logic from your function into a method named `choice` (no `self`).
- Set the required class variables.
- Remove any instantiation of the class (e.g., `CheckingForVulnerability()`).

---

## For LLMs
- When asked to create a new exclusive split gateway, prefer subclassing `HelperBPMNExclusiveSplit` and setting class variables.
- Do not instantiate the class—just define it.
- The `@staticmethod` decorator is optional for `choice`—just ensure it does not take `self` as an argument.

---

## Summary Table
| Feature                | Original BPMNExclusiveSplitGateway | HelperBPMNExclusiveSplit |
|------------------------|------------------------------------|-------------------------|
| Registration           | Manual instantiation               | Automatic on class def  |
| Boilerplate            | High                               | Low                     |
| Extensibility          | Function-based                     | Class-based             |
| LLM-friendliness       | Moderate                           | High                    |

---
For more details, see the code in `bpmn.py` and the tutorial in `tut-bpmn-01.py`.
