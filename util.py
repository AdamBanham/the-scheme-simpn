from simpn.simulator import SimProblem, SimToken

from joblib import Parallel, delayed 
from tqdm import tqdm

from random import choice as random_choice, normalvariate
from itertools import batched, product
from time import time as now
from copy import deepcopy

def pick_time(normally, dev=None) -> float:
    """
    Returns a a non-neg normally distribution sample from a 
    distribution with a mean of `normally` with a deviation 
    of `dev`. `dev` defaults to 1/4 of `normally` if not given.
    Minimum return value is 1/8 of the normally time.
    """
    if dev is None:
        dev = max(0.25, normally * 0.25)
    return max(
        (normally * (1/8.0)),
        normalvariate(normally, dev)
    )

def increment_priority(tok_values):
    """
    Increments the values of a token so the scheduler prioritise it more.
    """
    if len(tok_values) > 1:
        tok_values = (tok_values[0], tok_values[1]+1)
    else:
        tok_values = (tok_values[0], 1)
    return tok_values

class PriorityScheduler:
    
    def __init__(self, start_name, debug=False):
        self._start_name = start_name 
        self.pool = Parallel(n_jobs=-2)
        self._debug = debug

    def log(self, msg):
        if (self._debug):
            print(f"PriorityScheduler::{msg}")

    def __call__(self, bindings, *args, **kwds):

        if (len(bindings) < 2):
            # self.log("Short scheduling...")
            return bindings[0]

        self.log("Scheduling...")
        def count_actions(choice, name=self._start_name):
            actions = 0
            if isinstance(choice, SimToken):
                if isinstance(choice.value, tuple) and len(choice.value) > 1:

                    nested_values = False
                    for vals in choice.value:
                        nested_values = nested_values or isinstance(vals, tuple)
                        if nested_values:
                            break

                    if nested_values:
                        for vals in choice.value:
                            if not isinstance(vals, tuple):
                                continue
                            if name in vals[0]:
                                actions += vals[1]
                    else:
                        if name in choice.value[0]:
                            actions += choice.value[1]
            return actions
        
        def counter(bind):
            actions = 0
            for choice in bind[0][0]:
                actions += count_actions(choice)
            return actions

        def grabber(bind):
            return (counter(bind),bind)
        
        # if (len(bindings) > 100):
        #     queue = self.pool(
        #         delayed(grabber)(bind) for bind in bindings
        #     )
        # else:
        queue = [
            grabber(bind) for bind in bindings
        ]
        
        self.log("sorting...")
        queue = sorted(queue, key=lambda x: x[0], reverse=True)
        top_action = queue[0][0]
        self.log(f"selection for {top_action}...")
        top_choices = [ ]
        if top_action == 0:
            top_choices = bindings
        else:
            for (count, choice) in queue:
                if count < top_action:
                    break
                top_choices.append(choice)
        selected = random_choice(top_choices)
        self.log(f"selected one from {len(top_choices)}...")
        return selected
    
class ParallelSimProblem(SimProblem):
    """
    An attempt to speed up steps by taking advantage of the inherent
    parallism needed to process tasks
    """

    def __init__(self, debugging=True, binding_priority=lambda bindings: bindings[0]):
        super().__init__(debugging, binding_priority)
        
    def event_bindings(self, event):
        """
        Calculates the set of bindings that enables the given event.
        Each binding is a tuple ([(place, token), (place, token), ...], time) that represents a single enabling binding.
        A binding is
        a possible token combination (see token_combinations), for which the event's
        guard function evaluates to True. In case there is no guard function, any combination is also a binding.
        The time is the time at which the latest token is available.
        For example, if a event has incoming SimVar a and b with tokens 1@2 on a and 2@3, 3@1 on b,
        the possible bindings are ([(a, 1@2), (b, 2@3)], 3) and ([(a, 1@2), (b, 3@1)], 2)

        :param event: the event for which to calculate the enabling bindings.
        :return: list of tuples ([(place, token), (place, token), ...], time)
        """
        nr_incoming_places = len(event.incoming)
        if nr_incoming_places == 0:
            raise Exception("Though it is strictly speaking possible, we do not allow events like '" + str(self) + "' without incoming arcs.")

        bindings = [[]]
        place_token_products = [
            list(product([place], [ tok  for tok  in place.marking ]))
            for place in event.incoming
        ]
        bindings = product(*place_token_products)
        
        def handle(binding):
            variable_values = []
            time = None
            for (place, token) in binding:
                if (event.guard is not None):
                    variable_values.append(token.value)
                if time is None or token.time > time:
                    time = token.time
            return (binding, time, variable_values)

        # a binding must have all incoming places
        
        new_bindings = [
            handle(binding)
            for binding in bindings
            if len(binding) == nr_incoming_places
        ]
        bindings = new_bindings

        # if a event has a guard, only bindings are enabled for which the guard evaluates to True
        if event.guard is not None:
            result = [
                (binding, time)
                for (binding, time, variable_values)
                in new_bindings
                if event.guard(*variable_values)
            ]
        else :
            result = [
                (binding, time)
                for (binding, time, _)
                in new_bindings
            ]

        # result = []
        # for binding in bindings:
        #     variable_values = []
        #     time = None
        #     for (place, token) in binding:
        #         variable_values.append(token.value)
        #         if time is None or token.time > time:
        #             time = token.time
        #     enabled = True
        #     if event.guard is not None:
        #         try:
        #             enabled = event.guard(*variable_values)
        #         except Exception as e:
        #             raise TypeError("Event " + event + ": guard generates exception for values " + str(variable_values) + ".") from e
        #     if enabled:
        #         result.append((binding, time))

        return result

    def bindings(self):
        """
        Calculates the set of timed bindings that is enabled over all events in the problem.
        Each binding is a tuple ([(place, token), (place, token), ...], time, event) that represents a single enabling binding.
        If no timed binding is enabled at the current clock time, updates the current clock time to the earliest time at which there is.
        :return: list of tuples ([(place, token), (place, token), ...], time, event)
        """
        min_enabling_time = None

        # find the smallest largest enabling time for an event's
        # incoming markings
        timings = dict()
        for ev in self.events:
            smallest = []
            skip = False
            added = False
            
            for place in ev.incoming:
                try:
                    smallest.append(place.marking[0].time)
                    added = True
                except:
                    skip = True
            
            if (skip or not added):
                timings[ev] = 0
                continue

            smallest_largest = max(smallest)
            timings[ev] = smallest_largest

            if (smallest_largest == 0):
                continue

            # keep track of the smallest next possible clock
            if (smallest_largest is not None) \
                and (min_enabling_time is None \
                     or smallest_largest < min_enabling_time):
                min_enabling_time = smallest_largest 

        # timed bindings are only enabled if they have time <= clock
        # if there are no such bindings, set the clock to the earliest time at which there are
        if min_enabling_time is not None and min_enabling_time > self.clock:
            self.clock = min_enabling_time
        # We now also need to update the bindings, because the SimVarTime may have changed and needs to be updated.
        # TODO This is inefficient, because we are recalculating all bindings, while we only need to recalculate the ones that have SimVarTime in their inflow.
        timed_bindings = [] 
        for t, earlist in timings.items():
            if earlist > self.clock:
                continue
            for (binding, time) in self.event_bindings(t):
                if (time <= self.clock):
                    timed_bindings.append((binding, time, t))
        # now return the untimed bindings + the timed bindings that have time <= clock
        return timed_bindings
    
    def step(self):
        """
        Executes a single step of the simulation.
        If multiple events can happen, one is selected at random.
        Returns the binding that happened, or None if no event could happen.
        """
        start = now()
        bindings = self.bindings()
        end = now() - start 
        print(f"bindings took {end:0.4f}s")
        
        if len(bindings) > 0:
            start = now()
            timed_binding = self.binding_priority(bindings)
            end = now() - start 
            print(f"priority took {end:0.4f}s")
            start = now()
            self.fire(timed_binding)
            end = now() - start 
            print(f"firing took {end:0.4f}s")
            return timed_binding
        return None
    
    def simulate(self, duration, reporter=None):
        active_model = True
        custom_bar_format = '{l_bar}{bar}| {n:.1f}/{total:.1f} [{elapsed}<{remaining}, {rate_fmt}]'
        pbar = tqdm(
            desc="Simulating...", 
            total=duration,
            bar_format=custom_bar_format
        )
        while self.clock <= duration and active_model:
            last = self.clock
            bindings = self.bindings()
            if len(bindings) > 0:
                timed_binding = self.binding_priority(bindings)
                self.fire(timed_binding)
                if reporter is not None:
                    if type(reporter) == list:
                        for r in reporter:
                            r.callback(timed_binding)
                    else:
                        reporter.callback(timed_binding)
            else:
                active_model = False
            pbar.update(self.clock - last)
        pbar.close()

    