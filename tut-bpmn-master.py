from random import seed
seed(42)

from simpn.simulator import SimToken, SimProblem
from visualisation import Visualisation
from bpmn import BPMN
from util import PriorityScheduler, pick_time, increment_priority
from util import ParallelSimProblem as SimProblem

from simsettings import AGENTS, BACKLOG, DURATION, BATCHED, RATE
from random import uniform, choice as random_choice
from time import time
from os.path import join 
from sys import argv

LAYOUT_FILE = join(".", "tut-bpmn-master.layout")

TESTING = False
T_DURATION = DURATION / 4
RECORD = False

problem = SimProblem(
    binding_priority=PriorityScheduler("Intervention Loaded")
)

if (len(argv) < 2):
    print("missing argument for number of agents, using default of 25.")
else:
    AGENTS = int(argv[1])

class DHS(BPMN):
    type="resource-pool"
    model=problem
    name="dhs"
    amount=AGENTS

c1 = problem.add_var("exclusive-choice-1 queue")
gd_q = problem.add_var("generate-discr queue")
cr_q = problem.add_var("contact-recipient queue")
c2 = problem.add_var("contact-result-choice-2 queue")
tk_q = problem.add_var("recipient responds queue")
un_q = problem.add_var("unable-to-reach queue")
gc_q = problem.add_var("generate-contact-notice")
j1a = problem.add_var("exclusive-join-1-a")
j1b = problem.add_var("exclusive-join-1-b")
in_q = problem.add_var("issue notice queue")

done = problem.add_var("Recipient Contacted")
outreach_needed = problem.add_var("outreach needed")

class InterventionLoaded(BPMN):
    type="start"
    model = problem
    outgoing = [c1]
    amount = BATCHED
    name = "Intervention Loaded"

    def interarrival_time():
        return RATE
    
class GoodEnding(BPMN):
    type="event"
    model = problem 
    incoming = [done]
    outgoing = ["move to p2"]
    name = "end-event-1"

    def behaviour(c):
        return [SimToken(c)]

class BadEnding(BPMN):
    type="event"
    model = problem 
    incoming = [outreach_needed]
    outgoing = ["move to p3"]
    name = "end-event-2"

    def behaviour(c):
        return [SimToken(c)]

class GenerateDiscrepancy(BPMN):
    type="task"
    model = problem
    incoming = [gd_q, "dhs"]
    outgoing = [j1a, "dhs"]
    name = "Generate Discrepancy"

    def behaviour(c, r):
        c = increment_priority(c)
        return [SimToken((c, r), delay=pick_time(3))]


class ContactRecipient(BPMN):
    type="task"
    model = problem
    incoming = [cr_q, "dhs"]
    outgoing = [c2, "dhs"]
    name = "Contact Recipient"

    def behaviour(c, r):
        c = increment_priority(c)
        delay = pick_time(3)
        return [
            SimToken((c,r), delay=delay), 
        ]

class RecipientResponds(BPMN):
    type="event"
    model = problem 
    incoming = [tk_q, "dhs"]
    outgoing = [done, "dhs"]
    name = "Recipient responds"

    def behaviour(c, r):
        c = increment_priority(c)
        delay = pick_time(2)
        return [
            SimToken(c, delay=delay), 
            SimToken(r, delay=delay)
        ]
    
class UnableToContact(BPMN):
    type="event"
    model = problem
    incoming = [un_q,]
    outgoing = [gc_q,]
    name = "Unable to contact"

    def behaviour(c,):
        c = increment_priority(c)
        return [SimToken(c),]
    
class RecipientContactChoice(BPMN):
    type="gat-ex-split"
    model = problem
    incoming = [c2]
    outgoing = [un_q, tk_q]
    name = "Recipient Contact Event Gateway"

    def choice(c):
        pick = uniform(1, 100)
        if pick <= 20:
            wait = pick_time(16,2)
            return [ None, SimToken(c, delay=wait)]
        else:
            return [
                SimToken(c, delay=24), None
            ]
        
class GenerateContactNotice(BPMN):
    type="task"
    model = problem 
    incoming = [ gc_q , "dhs" ]
    outgoing = [ j1b, "dhs" ]
    name = "Generate Contact Notice"

    def behaviour(c, r):
        c = increment_priority(c)
        return [
            SimToken(
                (c,r), delay=pick_time(2)
            )
        ]

class CheckingForVulnerability(BPMN):
    type="gat-ex-split"
    model = problem
    incoming = [c1]
    outgoing = [gd_q, cr_q]
    name = "Checking for Vulnerability"

    def choice(c):
        pick = uniform(0, 100)
        if pick <= 67:
            return [SimToken(c), None]
        else:
            return [None, SimToken(c)]
        
class ExclusiveJoin1(BPMN):
    type="gat-ex-join"
    model = problem 
    incoming = [j1a, j1b]
    outgoing = [in_q]
    name = "exclusive-join-1"   

class IssueNotice(BPMN):
    type="task"
    model = problem
    incoming = [in_q, "dhs"]
    outgoing = [outreach_needed, "dhs"]
    name = "Issue Notice"

    def behaviour(c, r):
        c = increment_priority(c)
        return [SimToken((c, r), delay=pick_time(1))]
    
## phase three

c1 = problem.add_var("exclusive-choice-1")
r1 = problem.add_var("recipient initially responds")
d1 = problem.add_var("waiting-queue-21")
c2 = problem.add_var("exclusive-choice-2")
j1a = problem.add_var("exclusive-join-1a")
j1b = problem.add_var("exclusive-join-1b")
j2a = problem.add_var("exclusive-join-2a")
t1s = problem.add_var("check-start")
t2s = problem.add_var("suspend-start")
c3 = problem.add_var("exclusive-choice-3")
d2 = problem.add_var("waiting-queue-14")
r2 = problem.add_var("recipient responds")
j2b = problem.add_var("exclusive-join-2b")
t3s = problem.add_var("restore-start")

responded = problem.add_var("responded")
nonrespond = problem.add_var("nonrespond")

class InterventionLoaded(BPMN):
    type="event"
    model = problem
    incoming= ["move to p3"]
    outgoing = [c1]
    name = "Notice Issued"

    def behaviour(c):
        return [SimToken(c)]
    
class RecipientResponse1(BPMN):
    type="gat-ex-split"
    model = problem 
    incoming = [c1]
    outgoing = [r1,d1]
    name = "Does the recipient respond?"

    def choice(c):
        pick = uniform(1, 100)
        c = increment_priority(c)
        if pick <= 20:
            return [SimToken(c, delay=pick_time(7 * 8, 2 * 8)), None]
        else:
            return [None, SimToken(c, delay=21 * 8)]
        
class WaitFor21Days(BPMN):
    type="event"
    model = problem 
    incoming = [d1] 
    outgoing = [t1s]
    name = "21 Days"

    def behaviour(c):
        c = increment_priority(c)
        return [SimToken(c, delay=0.01)]
    
class CheckingForActive(BPMN):
    type="task"
    model = problem 
    incoming = [t1s, "dhs"]
    outgoing = [c2, "dhs"]
    name = "Check for active payments"

    def behaviour(c, r):
        c = increment_priority(c)
        return [SimToken((c,r), delay=pick_time(2))]

class RecipientCalls(BPMN):
    type="event"
    model = problem 
    incoming = [r1, "dhs"]
    outgoing = [j1a, "dhs"]
    name = "Recipient calls DHS"

    def behaviour(c , r):
        c = increment_priority(c)
        call_time = pick_time(2)
        return [
            SimToken(c, delay=call_time), 
            SimToken(r, delay=call_time)
        ]

class HasActivePayments(BPMN):
    type="gat-ex-split"
    model = problem 
    incoming = [c2]
    outgoing = [j2a,t2s]
    name = "does recipient have active payments?"

    def choice(c):
        pick = uniform(1, 100)
        c = increment_priority(c)
        if pick <= 20:
            return [SimToken(c), None]
        else:
            return [None, SimToken(c)]

class SuspendPayments(BPMN):
    type="task"
    model = problem 
    incoming = [t2s, "dhs"]
    outgoing = [c3, "dhs"]
    name = "Suspend payments and hold review"

    def behaviour(c, r):
        c = increment_priority(c)
        return [SimToken((c,r), delay=pick_time(2))]
    
class DoesRecipientRespond2(BPMN):
    type="gat-ex-split"
    model = problem 
    incoming = [c3]
    outgoing = [d2,r2]
    name = "Does the recipient respond"

    def choice(c):
        pick = uniform(1, 100)
        c = increment_priority(c)
        if pick <= 20:
            return [SimToken(c, delay=14*8), None]
        else:
            return [None, SimToken(c, pick_time(7*8, 2*8))]
        
class Waiting14Days(BPMN):
    type="event"
    model = problem 
    incoming = [d2]
    outgoing = [j2b]
    name = "14 days"

    def behaviour(c):
        c = increment_priority(c)
        return [SimToken(c, delay=0.01)]
    
class RecipientCallsIn(BPMN):
    type="event"
    model = problem 
    incoming = [r2, "dhs"]
    outgoing = [t3s, "dhs"]
    name = "Recipient Calls In"

    def behaviour(c, r):
        c = increment_priority(c)
        call_time = pick_time(2)
        return [
            SimToken(c, delay=call_time), 
            SimToken(r, delay=call_time)
        ]
    
class RestorePayments(BPMN):
    type="task"
    model = problem 
    incoming = [t3s, "dhs"]
    outgoing = [j1b, "dhs"]
    name = "Restore payments"

    def behaviour(c, r):
        c = increment_priority(c)
        return [SimToken((c,r), delay=pick_time(2))]
    
class ExclusiveJoin2(BPMN):
    type="gat-ex-join"
    model = problem 
    incoming = [j1a, j1b]
    outgoing = [responded]
    name = "Join-2"

class ExclusiveJoin(BPMN):
    type="gat-ex-join"
    model = problem 
    incoming = [j2a, j2b]
    outgoing = [nonrespond]
    name = "Join-1"

class RecipientResponded(BPMN):
    type="end"
    model = problem 
    incoming = [responded]
    name = "Recipient responded"

class RecipientResponded(BPMN):
    type="end"
    model = problem 
    incoming = [nonrespond]
    name = "Recipient did not responded"


## phase two -- confirmation

class ConfirmRecipient(BPMN):
    model=problem
    type="task"
    name="Confirm recipient identity"
    incoming=["move to p2" , "dhs"]
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






if TESTING:
    start = time()
    problem.simulate(T_DURATION)
    end = time() - start 
    print(f"simulation took {end:.3f} seconds...")

    vis = Visualisation(problem,
                        layout_algorithm="auto",
                        layout_file=LAYOUT_FILE,
                        record=True)
    vis.set_speed(200)
    vis.show()
    vis.save_layout(LAYOUT_FILE)

else:
    vis = Visualisation(problem,
                        layout_algorithm="auto",
                        layout_file=LAYOUT_FILE,
                        record=RECORD)
    vis.set_speed(2000)
    vis.show()
    vis.save_layout(LAYOUT_FILE)