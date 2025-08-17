from random import seed 
seed(42)

from simpn.simulator import SimToken, SimProblem
from visualisation import Visualisation
from util import PriorityScheduler, pick_time
from util import ParallelSimProblem as SimProblem
from util import increment_priority
from simsettings import AGENTS, DURATION, BACKLOG, BATCHED, RATE
from bpmn import BPMN

from os.path import join, exists
from random import uniform
from sys import argv

LAYOUT_FILE = join(".","tut-bpmn-04.layout")
RECORD = False
START_NAME = "third-party-collection"

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
    outgoing=["information required"]

    def interarrival_time():
        return RATE
    
class GenerateEmployerTask(BPMN):
    type="task"
    model=problem
    name="Generate employer information notice"
    incoming=[ "information required", "dhs" ]
    outgoing=[ "notice gen", "dhs" ]

    def behaviour(c,r):
        c = increment_priority(c)
        return [ SimToken((c,r), delay=pick_time(3)) ]

class IssueEmployerNoticeTask(BPMN):
    type="task"
    model=problem
    name="Issue notice to employer"
    incoming=[ "notice gen", "dhs" ]
    outgoing=[ "notice sent", "dhs" ]

    def behaviour(c,r):
        c = increment_priority(c)
        return [ SimToken((c,r), delay=pick_time(1)) ]

class EmployerResponseXorSplit(BPMN):
    type="gat-ex-split"
    model=problem
    name="Does the employer respond?"
    incoming=["notice sent"]
    outgoing=["employer nonresponse", "employer responds"]

    def choice(c):
        c = increment_priority(c)
        pick = uniform(0,100)
        if pick <= 80:
            return [SimToken(c, delay=14 * 8), None]
        else:
            return [None, SimToken(c, delay=pick_time(7 * 8, 2 * 8))]

class EmployerResponseInterEvent(BPMN):
    type="event"
    model=problem
    name="Employer returns documents"
    incoming=["employer responds"]
    outgoing=["employer returned documents"]

    def behaviour(c):
        event_time = 0.01   
        return [
            SimToken(c, delay=event_time),
        ]

class EmployerDeadlineInterEvent(BPMN):
    type="event"
    model=problem
    name="Employer Misses Deadline"
    incoming=["employer nonresponse"]
    outgoing=["employer deadline missed"]

    def behaviour(c):
        event_time = 0.01   
        return [
            SimToken(c, delay=event_time),
        ]

class ContactEmployerTask(BPMN):
    type="task"
    model=problem
    name="Contact Employer to discuss notice"
    incoming=[ "employer deadline missed", "dhs" ]
    outgoing=[ "contacted employer", "dhs" ]

    def behaviour(c,r):
        c = increment_priority(c)
        return [ SimToken((c,r), delay=pick_time(48)) ]

class CanEmployerProvideXorSplit(BPMN):
    type="gat-ex-split"
    model=problem
    name="Can or will the employer provide information?"
    incoming=["contacted employer"]
    outgoing=["employer will provide", "employer will not provide"]

    def choice(c):
        c = increment_priority(c)
        pick = uniform(0,100)
        if pick <= 80:
            return [SimToken(c), None]
        else:
            return [None, SimToken(c)]

class VerbalCollectFromEmployerTask(BPMN):
    type="task"
    model=problem
    name="Collect information verbally from employer"
    incoming=[ "employer will provide", "dhs" ]
    outgoing=[ "employer verbally collected", "dhs" ]

    def behaviour(c,r):
        c = increment_priority(c)
        return [ SimToken((c,r), delay=pick_time(2)) ]

class DefintelyInformationFromEmployerXorJoin(BPMN):
    type="gat-ex-join"
    model=problem
    name="Collected from employer"
    incoming=["employer verbally collected", "employer returned documents"]
    outgoing=["completed employer path"]

class GenerateATONoticeTask(BPMN):
    type="task"
    model=problem
    name="Generate ATO request notice"
    incoming=[ "employer will not provide", "dhs" ]
    outgoing=[ "ato notice gen", "dhs" ]

    def behaviour(c,r):
        c = increment_priority(c)
        return [ SimToken((c,r), delay=pick_time(5)) ]


class IssueATOTask(BPMN):
    type="task"
    model=problem
    name="Issue ATO notice"
    incoming=[ "ato notice gen", "dhs" ]
    outgoing=[ "ato notice issued", "dhs" ]

    def behaviour(c,r):
        c = increment_priority(c)
        return [ SimToken((c,r), delay=pick_time(1)) ]

class ATOReturnsInterEvent(BPMN):
    type="event"
    model=problem
    name="ATO returns documents"
    incoming=["ato notice issued"]
    outgoing=["ato path completed"]

    def behaviour(c):
        event_time = pick_time(3 * 8)
        return [
            SimToken(c, delay=event_time),
        ]

class CollectionCompletedXorJoin(BPMN):
    type="gat-ex-join"
    model=problem
    name="documents aquired"
    incoming=["ato path completed", "completed employer path"]
    outgoing=["collection done"]

class PhaseEnd(BPMN):
    type="end"
    name="Collection completed"
    model=problem
    incoming=["collection done"]

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
