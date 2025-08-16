from simpn.simulator import SimProblem, SimToken
from simpn.prototypes import BPMNStartEvent, BPMNEndEvent, BPMNTask
from visualisation import Visualisation

from random import uniform
from os.path import join, exists

LAYOUT_FILE = "aesthetics-a.layout"

problem = SimProblem()

p1 = problem.add_place("p1")
p2 = problem.add_place("p2")
r = problem.add_place("resources")
for i in range(3):
    r.put(f"resource-{i+1}")

def interarrival_time():
    return uniform(1, 2)
start = BPMNStartEvent(
    problem,
    [],
    [p1],
    "Start",
    interarrival_time
)

def behaviour(c,r):
    return [
        SimToken((c,r), delay=uniform(1,4))
    ]
task = BPMNTask(
    problem,
    [p1,r],
    [p2,r],
    "Task A",
    behaviour
)

end = BPMNEndEvent(
    problem,
    [p2],
    [],
    "Done"
)

if exists(LAYOUT_FILE):
    vis = Visualisation(problem, LAYOUT_FILE)
else:
    vis = Visualisation(problem)
    
vis.show()
vis.save_layout(LAYOUT_FILE)