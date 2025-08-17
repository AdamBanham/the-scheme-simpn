from random import seed
seed(42)

from simpn.simulator import SimToken
from simpn.simulator import SimProblem
from visualisation import Visualisation
from bpmn import BPMN
from util import PriorityScheduler, pick_time, increment_priority
from util import ParallelSimProblem as SimProblem

from random import uniform, choice as random_choice
from os.path import join 
from sys import argv
from time import time

TESTING = False
T_DURATION = 8

def work():

    LAYOUT_FILE = join(".", "tut-bpmn-02.layout")

    shop = SimProblem(
        binding_priority=PriorityScheduler("Notice Issued")
    )

    from simsettings import DURATION, BACKLOG, AGENTS, BATCHED, RATE

    if (len(argv) < 2):
        print("missing argument for number of agents, using default of 25.")
    else:
        AGENTS = int(argv[1])

    class DHS(BPMN):
        type="resource-pool"
        model=shop
        name="dhs"
        amount=AGENTS

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

    class InterventionLoaded(BPMN):
        type="start"
        model = shop
        outgoing = [c1]
        amount = BATCHED
        name = "Notice Issued"

        def interarrival_time():
            return RATE
        
    class RecipientResponse1(BPMN):
        type="gat-ex-split"
        model = shop 
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
        model = shop 
        incoming = [d1] 
        outgoing = [t1s]
        name = "21 Days"

        def behaviour(c):
            c = increment_priority(c)
            return [SimToken(c, delay=0.01)]
        
    class CheckingForActive(BPMN):
        type="task"
        model = shop 
        incoming = [t1s, "dhs"]
        outgoing = [c2, "dhs"]
        name = "Check for active payments"

        def behaviour(c, r):
            c = increment_priority(c)
            return [SimToken((c,r), delay=pick_time(2))]

    class RecipientCalls(BPMN):
        type="event"
        model = shop 
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
        model = shop 
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
        model = shop 
        incoming = [t2s, "dhs"]
        outgoing = [c3, "dhs"]
        name = "Suspend payments and hold review"

        def behaviour(c, r):
            c = increment_priority(c)
            return [SimToken((c,r), delay=pick_time(2))]
        
    class DoesRecipientRespond2(BPMN):
        type="gat-ex-split"
        model = shop 
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
        model = shop 
        incoming = [d2]
        outgoing = [j2b]
        name = "14 days"

        def behaviour(c):
            c = increment_priority(c)
            return [SimToken(c, delay=0.01)]
        
    class RecipientCallsIn(BPMN):
        type="event"
        model = shop 
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
        model = shop 
        incoming = [t3s, "dhs"]
        outgoing = [j1b, "dhs"]
        name = "Restore payments"

        def behaviour(c, r):
            c = increment_priority(c)
            return [SimToken((c,r), delay=pick_time(2))]
        
    class ExclusiveJoin2(BPMN):
        type="gat-ex-join"
        model = shop 
        incoming = [j1a, j1b]
        outgoing = [responded]
        name = "Join-2"

    class ExclusiveJoin(BPMN):
        type="gat-ex-join"
        model = shop 
        incoming = [j2a, j2b]
        outgoing = [nonrespond]
        name = "Join-1"

    class RecipientResponded(BPMN):
        type="end"
        model = shop 
        incoming = [responded]
        name = "Recipient responded"

    class RecipientResponded(BPMN):
        type="end"
        model = shop 
        incoming = [nonrespond]
        name = "Recipient did not responded"

    if TESTING:
        start = time()
        shop.simulate(T_DURATION)
        end = time() - start 
        print(f"simulation finished in {end:0.3f} seconds...")


        # vis = Visualisation(shop,
        #                     layout_algorithm="auto",
        #                     layout_file=LAYOUT_FILE,
        #                     record=False)
        # vis.show()

    else:
        vis = Visualisation(shop,
                            layout_algorithm="auto",
                            layout_file=LAYOUT_FILE,
                            record=False)
        vis.set_speed(2000)
        vis.show()
        vis.save_layout(LAYOUT_FILE)

if __name__ == "__main__":
    work()