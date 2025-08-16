from simpn.simulator import SimToken
from visualisation import Visualisation
from util import PriorityScheduler, pick_time, ParallelSimProblem
from util import increment_priority
from bpmn import BPMN

from os.path import join, exists
from random import uniform
from sys import argv

LAYOUT_FILE = join(".","tut-bpmn-xx.layout")
RECORD = False
START_NAME = "phase-start"

AGENTS = 25
BACKLOG = 1000000
DURATION = 8760
if (len(argv) < 2):
    print("missing argument for number of agents, using default of 25.")
else:
    AGENTS = int(argv[1])

problem = ParallelSimProblem(
    binding_priority=PriorityScheduler(START_NAME)
)

class DHS(BPMN):
    type="resource-pool"
    model=problem
    name="dhs"
    amount=AGENTS

class PhaseStart(BPMN):
    type="start"
    name=START_NAME
    model=problem
    outgoing=["phase started"]

    def interarrival_time():
        return DURATION / BACKLOG
    

class PhaseEnd(BPMN):
    type="end"
    name="phase-end"
    model=problem
    incoming=["phase ended"]


if exists(LAYOUT_FILE):
    vis = Visualisation(
        problem, LAYOUT_FILE,
        record=RECORD
    )
else:
    vis = Visualisation(
        problem, record=RECORD
    )
vis.set_speed(200)
vis.show()
vis.save_layout(LAYOUT_FILE)
