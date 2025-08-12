from simpn.simulator import SimProblem, SimToken

from random import choice as random_choice

class PriorityScheduler:

    def __init__(self, start_name):
        self._start_name = start_name 

    def log(self, msg):
        print(f"PriorityScheduler::{msg}")

    def __call__(self, bindings, *args, **kwds):

        if (len(bindings) < 2):
            # self.log("Short scheduling...")
            return bindings[0]

        self.log("Scheduling...")
        def count_actions(choice):
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
                            if self._start_name in vals[0]:
                                actions += vals[1]
                    else:
                        if self._start_name in choice.value[0]:
                            actions += choice.value[1]
            return actions
        
        def counter(bind):
            actions = 0
            for choice in bind[0][0]:
                actions += count_actions(choice)
            return actions

        def grabber(bind):
            return counter(bind)
        
        
        self.log("sorting...")
        queue = sorted(bindings, key=grabber, reverse=True)
        top_action = grabber(queue[0])
        self.log(f"selection for {top_action}...")
        top_choices = [ ]
        if top_action == 0:
            top_choices = queue
        else:
            for choice in queue:
                count = grabber(choice)
                if count < top_action:
                    break
                top_choices.append(choice)
        selected = random_choice(top_choices)
        self.log(f"selected one from {len(top_choices)}...")
        return selected