from random import seed 
seed(42)

from simpn.simulator import SimToken, SimProblem
from visualisation import Visualisation
from util import PriorityScheduler, pick_time
from util import ParallelSimProblem as SimProblem
from util import increment_priority
from bpmn import BPMN

from simsettings import AGENTS, DURATION, BACKLOG, BATCHED, RATE
from os.path import join, exists
from random import uniform
from sys import argv

LAYOUT_FILE = join(".","tut-bpmn-05.layout")
RECORD = False
START_NAME = "entitlement-assessment"


if (len(argv) < 2):
    print("missing argument for number of agents, using default of 25.")
else:
    AGENTS = int(argv[1])

problem = SimProblem(
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
    amount=BATCHED
    outgoing=["assessment started"]

    def interarrival_time():
        return RATE

class UpdateRecordTask(BPMN):
    type="task"
    model=problem
    name="Update record with additional information"
    incoming=[ "assessment started", "dhs" ]
    outgoing=[ "updated record", "dhs" ]

    def behaviour(c,r):
        c = increment_priority(c)
        return [ SimToken((c,r), delay=pick_time(8)) ]

class CalculateEntitlementsTask(BPMN):
    type="task"
    model=problem
    name="Calculate Entitlements"
    incoming=[ "updated record", "dhs" ]
    outgoing=[ "calculated entitlement", "dhs" ]

    def behaviour(c,r):
        c = increment_priority(c)
        return [ SimToken((c,r), delay=pick_time(8)) ]

class DebtXorSplit(BPMN):
    type="gat-ex-split"
    model=problem
    name="Did entitlement result in a debt?"
    incoming=["calculated entitlement"]
    outgoing=["resulted in debt", "no debt raised"]

    def choice(c):
        c = increment_priority(c)
        pick = uniform(0,100)
        if pick <= 90:
            return [SimToken(c), None]
        else:
            return [None, SimToken(c)]

class RaiseDebtTask(BPMN):
    type="task"
    model=problem
    name="Raise Debt"
    incoming=[ "resulted in debt", "dhs" ]
    outgoing=[ "raised debt", "dhs" ]

    def behaviour(c,r):
        c = increment_priority(c)
        return [ SimToken((c,r), delay=pick_time(4)) ]

class PenaltyXorSplit(BPMN):
    type="gat-ex-split"
    model=problem
    name="Include Penalty"
    incoming=["raised debt"]
    outgoing=["include penalty", "no penalty"]

    def choice(c):
        c = increment_priority(c)
        pick = uniform(0,100)
        if pick <= 5:
            return [SimToken(c), None]
        else:
            return [None, SimToken(c)]

class AddPenaltyTask(BPMN):
    type="task"
    model=problem
    name="Add 10% penalty to debt"
    incoming=[ "include penalty", "dhs" ]
    outgoing=[ "included penalty", "dhs" ]

    def behaviour(c,r):
        c = increment_priority(c)
        return [ SimToken((c,r), delay=pick_time(0.5)) ]

class PenaltyXorJoin(BPMN):
    type="gat-ex-join"
    model=problem
    name="join-penalty"
    incoming=["included penalty", "no penalty"]
    outgoing=["ready to notify"]

class NotifyRecipientTask(BPMN):
    type="task"
    model=problem
    name="Notify recipient of debt outcome"
    incoming=[ "ready to notify", "dhs" ]
    outgoing=[ "notified of debt", "dhs" ]

    def behaviour(c,r):
        c = increment_priority(c)
        return [ SimToken((c,r), delay=pick_time(2)) ]    

class DebtRaisedEnd(BPMN):
    type="end"
    name="Debt raised"
    model=problem
    incoming=["notified of debt"]

class NoDebtEndEvent(BPMN):
    type="end"
    model=problem
    name="No Debt"
    incoming=["no debt raised"]

if exists(LAYOUT_FILE):
    vis = Visualisation(
        problem, LAYOUT_FILE,
        record=RECORD
    )
else:
    vis = Visualisation(
        problem, record=RECORD
    )
vis.set_speed(2000)
vis.show()
vis.save_layout(LAYOUT_FILE)
