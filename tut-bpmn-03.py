from random import seed
seed(42)

from simsettings import BACKLOG, DURATION, AGENTS

from simpn.simulator import SimToken, SimProblem
from visualisation import Visualisation
from util import PriorityScheduler, pick_time
from util import ParallelSimProblem as SimProblem
from util import increment_priority
from bpmn import BPMN

from os.path import join, exists
from random import uniform
from sys import argv

LAYOUT_FILE = join(".","tut-bpmn-03.layout")
RECORD = False
START_NAME = "confirmation"

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
    outgoing=["phase started"]

    def interarrival_time():
        return DURATION / BACKLOG
    
class ConfirmRecipient(BPMN):
    model=problem
    type="task"
    name="Confirm recipient identity"
    incoming=["phase started" , "dhs"]
    outgoing=["gat-xor-split-1", "dhs"]

    def behaviour(c, r):
        c = increment_priority(c)
        return [
            SimToken((c,r), delay=pick_time(2))
        ]
    
class IdentityXorSplit(BPMN):
    type="gat-ex-split"
    model=problem
    name="Identity Confirmed?"
    incoming=["gat-xor-split-1"]
    outgoing=["split-1a", "split-1b"]

    def choice(c):
        c = increment_priority(c)
        pick = uniform(0,100)
        if pick <= 80:
            return [SimToken(c), None]
        else:
            return [None, SimToken(c)]
        
class CollectInformationTask(BPMN):
    type="task"
    model=problem
    name="Collect information about discrepancy"
    incoming=[ "split-1a", "dhs" ]
    outgoing=[ "collected", "dhs" ]

    def behaviour(c,r):
        c = increment_priority(c)
        return [ SimToken((c,r), delay=pick_time(5)) ]
    
class ProvidedInformationXorSplit(BPMN):
    type="gat-ex-split"
    model=problem
    name="Provided Additional Information?"
    incoming=["collected"]
    outgoing=["split-2a", "split-2b"]

    def choice(c):
        c = increment_priority(c)
        pick = uniform(0,100)
        if pick <= 80:
            return [SimToken(c), None]
        else:
            return [None, SimToken(c)]
        
class AssessInformationTask(BPMN):
    type="task"
    model=problem
    name="Assess Additional information"
    incoming=[ "split-2a", "dhs" ]
    outgoing=[ "assessed", "dhs" ]

    def behaviour(c,r):
        c = increment_priority(c)
        return [ SimToken((c,r), delay=pick_time(5)) ]

class AcceptableInformationXorSplit(BPMN):
    type="gat-ex-split"
    model=problem
    name="Is information acceptable and reasonable?"
    incoming=["assessed"]
    outgoing=["split-3a", "split-3b"]

    def choice(c):
        c = increment_priority(c)
        pick = uniform(0,100)
        if pick <= 80:
            return [SimToken(c), None]
        else:
            return [None, SimToken(c)]

class RequestSupportTask(BPMN):
    type="task"
    model=problem
    name="Request support documents"
    incoming=[ "split-3b", "dhs" ]
    outgoing=[ "event-split", "dhs" ]

    def behaviour(c,r):
        c = increment_priority(c)
        return [ SimToken((c,r), delay=pick_time(1)) ]

class RecieveDocsXorSplit(BPMN):
    type="gat-ex-split"
    model=problem
    name="Documents Returned?"
    incoming=["event-split"]
    outgoing=["missing deadline", "documents returning"]

    def choice(c):
        c = increment_priority(c)
        pick = uniform(0,100)
        if pick <= 80:
            return [SimToken(c, delay=14 * 8), None]
        else:
            return [None, SimToken(c, delay=pick_time(7 * 8, 2 * 8))]

class MissedDeadlineInterEvent(BPMN):
    type="event"
    model=problem
    name="Agreed period for documents"
    incoming=["missing deadline"]
    outgoing=["missed deadline"]

    def behaviour(c):
        event_time = 0.01
        return [
            SimToken(c, delay=event_time),
        ]
    
class RecipientReturnsInterEvent(BPMN):
    type="event"
    model=problem
    name="Recipient provided documents"
    incoming=["documents returning"]
    outgoing=["documents returned"]

    def behaviour(c):
        event_time = 0.01
        return [
            SimToken(c, delay=event_time),
        ]
    
class AssessedReturnedTask(BPMN):
    type="task"
    model=problem
    name="Assess returned documents"
    incoming=[ "documents returned", "dhs" ]
    outgoing=[ "returned assessed", "dhs" ]

    def behaviour(c,r):
        c = increment_priority(c)
        return [ SimToken((c,r), delay=pick_time(5)) ]

class AcceptableReturnedXorSplit(BPMN):
    type="gat-ex-split"
    model=problem
    name="Are the returned documents acceptable?"
    incoming=["returned assessed"]
    outgoing=["returned accepted" , "returned rejected"]

    def choice(c):
        c = increment_priority(c)
        pick = uniform(0,100)
        if pick <= 80:
            return [SimToken(c), None]
        else:
            return [None, SimToken(c)]

class CollectedInformationXorJoin(BPMN):
    type="gat-ex-join"
    model=problem
    name="information collected"
    incoming=["split-3a", "returned accepted"]
    outgoing=["information-collected"]



class ManualXorJoin(BPMN):
    type="gat-ex-join"
    model=problem
    name="manual-join"
    incoming=["split-2b","missed deadline", "returned rejected"]
    outgoing=["manual-joiner"]

class SignalXorJoin(BPMN):
    type="gat-ex-join"
    model=problem
    name="signal-join"
    incoming=["manual-joiner", "split-1b"]
    outgoing=["signal-manual"]

class ManualAssessmentEndEvent(BPMN):
    type="end"
    model=problem
    name="Manual Assessment Required"
    incoming=["signal-manual"]


class PhaseEnd(BPMN):
    type="end"
    name="Recipient provided acceptable information"
    model=problem
    incoming=["information-collected"]

if exists(LAYOUT_FILE):
    vis = Visualisation(
        problem, LAYOUT_FILE,
        record=RECORD
    )
else:
    vis = Visualisation(
        problem, record=RECORD
    )
vis.set_speed(20)
vis.show()
vis.save_layout(LAYOUT_FILE)
