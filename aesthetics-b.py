from bpmn import BPMN
from simpn.simulator import SimProblem, SimToken
from util import pick_time
from visualisation import Visualisation

from random import uniform, normalvariate
from os.path import join, exists

LAYOUT_FILE = "aesthetics-b.layout"

prob = SimProblem()

class Start(BPMN):
    type="start"
    model=prob
    name="Started"
    outgoing=["p1"]

    def interarrival_time():
        return pick_time(3)
    
class Resources(BPMN):
    type="resource-pool"
    model=prob 
    name="resources"
    amount=5

class Task(BPMN):
    type="task"
    model=prob
    name="task-1"
    incoming=["p1", "resources"]
    outgoing=["p2", "resources"]

    def behaviour(c, r):
        return [ SimToken((c,r), delay=pick_time(5)) ]
    
class Split(BPMN):
    type="gat-ex-split"
    model=prob 
    name="Which way?"
    incoming=["p2"]
    outgoing=["left-1","right-1"]

    def choice(c):
        pick = uniform(0,100)
        if pick < 33:
            return [ SimToken(c), None ]
        else:
            return [ None, SimToken(c) ]
        
class TaskLeft(BPMN):
    type="task"
    model=prob
    name="Leftovers"
    incoming=["left-1", "resources"]
    outgoing=["join-1a", "resources"]

    def behaviour(c , r):
        return [ SimToken((c,r), delay=pick_time(4.5))]
    
class TaskRight(BPMN):
    type="task"
    model=prob
    name="Righters"
    incoming=["right-1", "resources"]
    outgoing=["join-1b", "resources"]

    def behaviour(c , r):
        return [ SimToken((c,r), delay=pick_time(3))]
    
class Join1(BPMN):
    type="gat-ex-join"
    model=prob
    name="join-1"
    incoming=["join-1a","join-1b"]
    outgoing=["checking"]

class CheckForInformation(BPMN):
    type="task"
    model=prob 
    name="Check for extras"
    incoming=["checking", "resources"]
    outgoing=["event-gat-start", "resources"]

    def behaviour(c, r):
        return [SimToken((c,r), delay=pick_time(5))]

class EventGatSpilt(BPMN):
    type="gat-ex-split"
    model=prob
    name="waiting for user"
    incoming = ["event-gat-start"]
    outgoing = ["user responds queue", "user not responsive"]

    def choice(c):
        pick = uniform(0, 100)
        if pick <= 60:
            return [SimToken(c,delay=pick_time(12,3)), None]
        else:
            return [None, SimToken(c)]
        
class UserInformation(BPMN):
    type="event"
    model=prob
    name="User Comms"
    incoming=["user responds queue", "resources"]
    outgoing=["event-gat-join-1a", "resources"]

    def behaviour(c, r):
        talk_time = pick_time(3)
        return [ SimToken(c, delay=talk_time), SimToken(r, delay=talk_time) ]

class UserNonresponsive(BPMN):
    type="event"
    model=prob 
    name="18 Hours"
    incoming=["user not responsive"]
    outgoing=["event-gat-join-1b"]

    def behaviour(c):
        return [ SimToken(c, delay=18) ]

class EventGatJoin(BPMN):
    type="gat-ex-join"
    model=prob
    name="join-2"
    incoming=["event-gat-join-1a", "event-gat-join-1b"]
    outgoing=["pre-end"]
    
class End(BPMN):
    type="end"
    model=prob 
    name="Ended"
    incoming=["pre-end"]
    

vis = None
if (exists(LAYOUT_FILE)):
    vis = Visualisation(prob, layout_file=LAYOUT_FILE, record=False)
else:
    vis = Visualisation(prob)
vis.set_speed(2000)
vis.show()
vis.save_layout(LAYOUT_FILE)