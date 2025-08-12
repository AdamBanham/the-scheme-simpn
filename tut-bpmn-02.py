from simpn.simulator import SimProblem, SimToken
from visualisation import Visualisation
from bpmn import HelperBPMNTask, HelperBPMNStart
from bpmn import HelperBPMNExclusiveSplit, HelperBPMNIntermediateEvent
from bpmn import HelperBPMNEnd, HelperBPMNExclusiveJoin
from util import PriorityScheduler

from math import exp
from random import uniform, choice as random_choice
from os.path import join 
from sys import argv

LAYOUT_FILE = join(".", "tut-bpmn-02.layout")

shop = SimProblem(
    binding_priority=PriorityScheduler("Notice Issued")
)

AGENTS = 25
BACKLOG = 1000000
DURATION = 8760
if (len(argv) < 2):
    print("missing argument for number of agents, using default of 25.")
else:
    AGENTS = int(argv[1])
dhs = shop.add_var("DHS Agents")
for i in range(AGENTS):
    dhs.put(f"dhs-{i+1}")

c1 = shop.add_var("exclusive-choice-1")
r1 = shop.add_var("recipient initially responds")
d1 = shop.add_var("waiting-queue-21")
c2 = shop.add_var("exclusive-choice-2")
j1a = shop.add_var("exclusive-join-1a")
j1b = shop.add_var("exclusive-join-1b")
j2a = shop.add_var("exclusive-join-2a")
t1s = shop.add_var("check-start")
t2s = shop.add_var("suspend-start")
c3 = shop.add_var("exclusive-choice-3")
d2 = shop.add_var("waiting-queue-14")
r2 = shop.add_var("recipient responds")
j2b = shop.add_var("exclusive-join-2b")
t3s = shop.add_var("restore-start")

responded = shop.add_var("responded")
nonrespond = shop.add_var("nonrespond")

class InterventionLoaded(HelperBPMNStart):
    model = shop
    outgoing = [c1]
    name = "Notice Issued"

    def interarrival_time():
        return DURATION / BACKLOG
    
class RecipientResponse1(HelperBPMNExclusiveSplit):
    model = shop 
    incoming = [c1]
    outgoing = [r1,d1]
    name = "Does the recipient respond?"

    def choice(c):
        pick = uniform(1, 100)
        if len(c) > 1:
            c = (c[0], c[1]+1)
        else:
            c = (c[0], 1)
        if pick <= 20:
            return [SimToken(c), None]
        else:
            return [None, SimToken(c)]
        
class WaitFor21Days(HelperBPMNIntermediateEvent):
    model = shop 
    incoming = [d1] 
    outgoing = [t1s]
    name = "21 Days"

    def behaviour(c):
        if len(c) > 1:
            c = (c[0], c[1]+1)
        else:
            c = (c[0], 1)
        return [SimToken(c, delay=2)]#delay=21 * 24)]
    
class CheckingForActive(HelperBPMNTask):
    model = shop 
    incoming = [t1s, dhs]
    outgoing = [c2, dhs]
    name = "Check for active payments"

    def behaviour(c, r):
        if len(c) > 1:
            c = (c[0], c[1]+1)
        else:
            c = (c[0], 1)
        return [SimToken((c,r), delay=exp(1/2))]

class RecipientCalls(HelperBPMNIntermediateEvent):
    model = shop 
    incoming = [r1, dhs]
    outgoing = [j1a, dhs]
    name = "Recipient calls DHS"

    def behaviour(c , r):
        if len(c) > 1:
            c = (c[0], c[1]+1)
        else:
            c = (c[0], 1)
        return [SimToken(c, delay=exp(1/2)), SimToken(r, delay=exp(1/2))]

class HasActivePayments(HelperBPMNExclusiveSplit):
    model = shop 
    incoming = [c2]
    outgoing = [j2a,t2s]
    name = "does recipient have active payments?"

    def choice(c):
        pick = uniform(1, 100)
        if len(c) > 1:
            c = (c[0], c[1]+1)
        else:
            c = (c[0], 1)
        if pick <= 20:
            return [SimToken(c), None]
        else:
            return [None, SimToken(c)]

class SuspendPayments(HelperBPMNTask):
    model = shop 
    incoming = [t2s, dhs]
    outgoing = [c3, dhs]
    name = "Suspend payments and hold review"

    def behaviour(c, r):
        if len(c) > 1:
            c = (c[0], c[1]+1)
        else:
            c = (c[0], 1)
        return [SimToken((c,r), delay=exp(1/2))]
    
class DoesRecipientRespond2(HelperBPMNExclusiveSplit):
    model = shop 
    incoming = [c3]
    outgoing = [d2,r2]
    name = "Does the recipient respond"

    def choice(c):
        pick = uniform(1, 100)
        if len(c) > 1:
            c = (c[0], c[1]+1)
        else:
            c = (c[0], 1)
        if pick <= 20:
            return [SimToken(c), None]
        else:
            return [None, SimToken(c)]
        
class Waiting14Days(HelperBPMNIntermediateEvent):
    model = shop 
    incoming = [d2]
    outgoing = [j2b]
    name = "14 days"

    def behaviour(c):
        if len(c) > 1:
            c = (c[0], c[1]+1)
        else:
            c = (c[0], 1)
        return [SimToken((c), delay=2)]#14*24)]
    
class RecipientCallsIn(HelperBPMNIntermediateEvent):
    model = shop 
    incoming = [r2, dhs]
    outgoing = [t3s, dhs]
    name = "Recipient Calls In"

    def behaviour(c, r):
        if len(c) > 1:
            c = (c[0], c[1]+1)
        else:
            c = (c[0], 1)
        return [SimToken(c, delay=exp(1/2)), SimToken(r, delay=exp(1/2))]
    
class RestorePayments(HelperBPMNTask):
    model = shop 
    incoming = [t3s, dhs]
    outgoing = [j1b, dhs]
    name = "Restore payments"

    def behaviour(c, r):
        if len(c) > 1:
            c = (c[0], c[1]+1)
        else:
            c = (c[0], 1)
        return [SimToken((c,r), delay=exp(1/2))]
    
class ExclusiveJoin2(HelperBPMNExclusiveJoin):
    model = shop 
    incoming = [j1a, j1b]
    outgoing = [responded]
    name = "Join-2"

class ExclusiveJoin(HelperBPMNExclusiveJoin):
    model = shop 
    incoming = [j2a, j2b]
    outgoing = [nonrespond]
    name = "Join-1"

class RecipientResponded(HelperBPMNEnd):
    model = shop 
    incoming = [responded]
    name = "Recipient responded"

class RecipientResponded(HelperBPMNEnd):
    model = shop 
    incoming = [nonrespond]
    name = "Recipient did not responded"
    
vis = Visualisation(shop,
                    layout_algorithm="auto",
                    layout_file=LAYOUT_FILE,
                    record=True)
vis.show()
vis.save_layout(LAYOUT_FILE)