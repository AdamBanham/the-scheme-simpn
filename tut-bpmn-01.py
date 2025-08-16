from random import seed
seed(42)

from simpn.simulator import SimToken
from visualisation import Visualisation
from bpmn import BPMN
from util import PriorityScheduler, pick_time, increment_priority
from util import ParallelSimProblem as SimProblem

from simsettings import AGENTS, BACKLOG, DURATION
from random import uniform, choice as random_choice
from os.path import join 
from sys import argv

LAYOUT_FILE = join(".", "tut-bpmn-01.layout")

shop = SimProblem(
    binding_priority=PriorityScheduler("Intervention Loaded")
)

if (len(argv) < 2):
    print("missing argument for number of agents, using default of 25.")
else:
    AGENTS = int(argv[1])

class DHS(BPMN):
    type="resource-pool"
    model=shop
    name="dhs"
    amount=AGENTS

c1 = shop.add_var("exclusive-choice-1 queue")
gd_q = shop.add_var("generate-discr queue")
cr_q = shop.add_var("contact-recipient queue")
c2 = shop.add_var("contact-result-choice-2 queue")
tk_q = shop.add_var("recipient responds queue")
un_q = shop.add_var("unable-to-reach queue")
gc_q = shop.add_var("generate-contact-notice")
j1a = shop.add_var("exclusive-join-1-a")
j1b = shop.add_var("exclusive-join-1-b")
in_q = shop.add_var("issue notice queue")

done = shop.add_var("Recipient Contacted")
outreach_needed = shop.add_var("outreach needed")

class InterventionLoaded(BPMN):
    type="start"
    model = shop
    outgoing = [c1]
    name = "Intervention Loaded"

    def interarrival_time():
        return DURATION / BACKLOG
    
class GoodEnding(BPMN):
    type="end"
    model = shop 
    incoming = [done]
    name = "end-event-1"

class BadEnding(BPMN):
    type="end"
    model = shop 
    incoming = [outreach_needed]
    name = "end-event-2"

class GenerateDiscrepancy(BPMN):
    type="task"
    model = shop
    incoming = [gd_q, "dhs"]
    outgoing = [j1a, "dhs"]
    name = "Generate Discrepancy"

    def behaviour(c, r):
        c = increment_priority(c)
        return [SimToken((c, r), delay=pick_time(3))]


class ContactRecipient(BPMN):
    type="event"
    model = shop
    incoming = [cr_q, "dhs"]
    outgoing = [c2, "dhs"]
    name = "Contact Recipient"

    def behaviour(c, r):
        c = increment_priority(c)
        delay = pick_time(3)
        return [
            SimToken(c, delay=delay), 
            SimToken(r, delay=delay)
        ]

class RecipientResponds(BPMN):
    type="event"
    model = shop 
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
    model = shop
    incoming = [un_q,]
    outgoing = [gc_q,]
    name = "Unable to contact"

    def behaviour(c,):
        c = increment_priority(c)
        return [SimToken(c),]
    
class RecipientContactChoice(BPMN):
    type="gat-ex-split"
    model = shop
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
    model = shop 
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
    model = shop
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
    model = shop 
    incoming = [j1a, j1b]
    outgoing = [in_q]
    name = "exclusive-join-1"   

class IssueNotice(BPMN):
    type="task"
    model = shop
    incoming = [in_q, "dhs"]
    outgoing = [outreach_needed, "dhs"]
    name = "Issue Notice"

    def behaviour(c, r):
        c = increment_priority(c)
        return [SimToken((c, r), delay=pick_time(1))]

vis = Visualisation(shop,
                    layout_algorithm="auto",
                    layout_file=LAYOUT_FILE,
                    record=False)
vis.set_speed(20)
vis.show()
vis.save_layout(LAYOUT_FILE)