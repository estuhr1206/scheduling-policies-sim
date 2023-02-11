#!/usr/bin/env python
"""client object for instances of clients in the breakwater system."""

import math
from collections import deque

# likely initialize clients in simulation_state.py, (similar to things like the sim_queues)
# list of them can be accessed in main simulation (and thereby breakwater_server, would it work as a param?)


class BreakwaterClient:

    def __init__(self, state):
        # Where tasks from task creation are placed once they have "arrived"
        self.queue = deque()
        # credits are incremented by server, decremented(used) by client
        self.credits = 0
        # equivalent to number of requests in queue
        self.current_demand = 0
        self.registered = False
        self.state = state

    def enqueue_task(self, task):
        self.queue.append(task)
        self.current_demand += 1

        if not self.registered:
            self.state.breakwater_server.client_register(self)
            self.registered = True
        # can be called from simulation, using the task generated by simulation state's initialize
        # tasks from that main list will get enqueued at random clients

        # should call spend_credits
        if self.credits > 0:
            self.spend_credits()

    # can instead call the server's register function
    # def register_with_server(self):
    #     pass

    def spend_credits(self):

        pass

    def deregister_with_server(self):
        pass

    def add_credit(self):
        self.credits += 1
        # should call spend credits
        self.spend_credits()

