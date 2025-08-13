from simpn.simulator import SimToken
from visualisation import Visualisation
from bpmn import HelperBPMNTask, HelperBPMNStart
from bpmn import HelperBPMNExclusiveSplit, HelperBPMNIntermediateEvent
from bpmn import HelperBPMNEnd, HelperBPMNExclusiveJoin
from util import PriorityScheduler
from util import ParallelSimProblem as SimProblem


from math import exp
from random import uniform, choice as random_choice
from os.path import join 
from sys import argv

LAYOUT_FILE = join(".", "tut-bpmn-01.layout")

shop = SimProblem(
    binding_priority=PriorityScheduler("Intervention Loaded")
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

class InterventionLoaded(HelperBPMNStart):
    model = shop
    outgoing = [c1]
    name = "Intervention Loaded"

    def interarrival_time():
        return DURATION / BACKLOG
    
class GoodEnding(HelperBPMNEnd):
    model = shop 
    incoming = [done]
    name = "end-event-1"

class BadEnding(HelperBPMNEnd):
    model = shop 
    incoming = [outreach_needed]
    name = "end-event-2"

class GenerateDiscrepancy(HelperBPMNTask):
    model = shop
    incoming = [gd_q, dhs]
    outgoing = [j1a, dhs]
    name = "Generate Discrepancy"

    def behaviour(c, r):
        if len(c) > 1:
            c = (c[0], c[1]+1)
        else:
            c = (c[0], 1)
        return [SimToken((c, r), delay=exp(1/3))]


class ContactRecipient(HelperBPMNIntermediateEvent):
    model = shop
    incoming = [cr_q, dhs]
    outgoing = [c2, dhs]
    name = "Contact Recipient"

    def behaviour(c, r):
        if len(c) > 1:
            c = (c[0], c[1]+1)
        else:
            c = (c[0], 1)
        return [SimToken(c, delay=exp(1/3)), SimToken(r, delay=exp(1/3))]

class RecipientResponds(HelperBPMNIntermediateEvent):
    model = shop 
    incoming = [tk_q, dhs]
    outgoing = [done, dhs]
    name = "Recipient responds"

    def behaviour(c, r):
        if len(c) > 1:
            c = (c[0], c[1]+1)
        else:
            c = (c[0], 1)
        return [SimToken(c, delay=exp(1/2)), SimToken(r, delay=exp(1/2))]
    
class UnableToContact(HelperBPMNIntermediateEvent):
    model = shop
    incoming = [un_q, dhs]
    outgoing = [gc_q, dhs]
    name = "Unable to contact"

    def behaviour(c, r):
        if len(c) > 1:
            c = (c[0], c[1]+1)
        else:
            c = (c[0], 1)
        return [SimToken(c), SimToken(r)]
    
class RecipientContactChoice(HelperBPMNExclusiveSplit):
    model = shop
    incoming = [c2]
    outgoing = [un_q, tk_q]
    name = "Recipient Contact Event Gateway"

    def choice(c):
        pick = uniform(1, 100)
        if pick <= 20:
            wait = exp(1/23)
            return [ None, SimToken(c, delay=wait)]
        else:
            return [
                SimToken(c, delay=24), None
            ]
        
class GenerateContactNotice(HelperBPMNTask):
    model = shop 
    incoming = [ gc_q , dhs ]
    outgoing = [ j1b, dhs ]
    name = "Generate Contact Notice"

    def behaviour(c, r):
        if len(c) > 1:
            c = (c[0], c[1]+1)
        else:
            c = (c[0], 1)
        return [
            SimToken(
                (c,r), delay=exp(1/2)
            )
        ]

class CheckingForVulnerability(HelperBPMNExclusiveSplit):
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
        
class ExclusiveJoin1(HelperBPMNExclusiveJoin):
    model = shop 
    incoming = [j1a, j1b]
    outgoing = [in_q]
    name = "exclusive-join-1"   

class IssueNotice(HelperBPMNTask):
    model = shop
    incoming = [in_q, dhs]
    outgoing = [outreach_needed, dhs]
    name = "Issue Notice"

    def behaviour(c, r):
        if len(c) > 1:
            c = (c[0], c[1]+1)
        else:
            c = (c[0], 1)
        return [SimToken((c, r), delay=exp(1/1))]

vis = Visualisation(shop,
                    layout_algorithm="auto",
                    layout_file=LAYOUT_FILE,
                    record=False)
vis.show()
vis.save_layout(LAYOUT_FILE)