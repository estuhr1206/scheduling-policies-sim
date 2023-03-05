#!/usr/bin/env python
"""client object for instances of clients in the breakwater system."""

import math
from collections import deque
import random

# clients are initialized in simulation_state.py, (similar to items like the sim_queues)
# list of them can be accessed in main simulation, from sim.state


class BreakwaterClient:

    def __init__(self, state, identifier):
        # Where tasks from task creation are placed once they have "arrived"
        self.queue = deque()
        # credits are incremented by server, decremented(used) by client. used as Cx from paper calculations
        # self.credits = 0
        # v3, adding in concept of credits in use and credits unused
        self.window = 0
        self.c_in_use = 0
        self.c_unused = 0
        # equivalent to number of requests in queue
        self.current_demand = 0
        self.registered = False
        self.state = state
        self.dropped_tasks = 0
        self.total_tasks = 0
        self.cores_at_drops = []
        self.tasks_spent_control_loop = 0

        self.id = identifier

    def enqueue_task(self, task):
        self.queue.append(task)
        self.current_demand += 1
        self.total_tasks += 1
        if not self.registered:
            self.state.breakwater_server.client_register(self)
            self.registered = True
        # can be called from simulation, using the task generated by simulation state's initialize
        # tasks from that main list will get enqueued at random clients

        # should call spend_credits
        if self.c_unused > 0:
            self.spend_credits()
        elif self.c_unused < 0:
            # print out that something is wrong
            raise ValueError("error, credits < 0")

    def spend_credits(self, from_control_loop=False):

        # upon no demand
        if self.current_demand <= 0:
            # TODO do nothing, don't deregister for debugging
            # self.deregister()
            # if < 0, something is wrong.
            if self.current_demand < 0:
                raise ValueError('error, demand was below 0')
            return False
        else:
            if from_control_loop:
                self.tasks_spent_control_loop += 1
            # aqm can happen here, simply don't enqueue it at a core if delay is high
            # self.state.breakwater_server.credits_issued -= 1
            self.c_unused -= 1
            self.c_in_use += 1

            current_task = self.queue.popleft()
            self.current_demand -= 1

            # check for aqm, if aqm, add some stat for request got dropped
            # breakwater paper: "AQM threshold to 2 · dt (e.g., dt = 80 μs and AQM threshold = 160 μs)"
            # TODO changing to use current system delay info
            """
                option1: use max delay of queues
                option2: use delay of chosen queue
            """
            chosen_queue = random.choice(self.state.available_queues)
            # delay = self.state.queues[chosen_queue].current_delay()
            delay = self.state.max_queue_delay()
            if delay <= 2 * self.state.config.BREAKWATER_TARGET_DELAY:
                # need to override arrival time for core usage
                # this is ok, because the arrival time usage for enqueuing at clients occurs before this
                # override here
                current_task.arrival_time = self.state.timer.get_time()
                current_task.source_client = self.id
                # enqueue at core
                self.state.queues[chosen_queue].enqueue(current_task, set_original=True)
            else:
                # shouldn't be dropped if load is low (aka the 50%)
                """
                    TODO possible for client to get x credits, and try to spend x times and have it fail each time
                    actually, that seems ok, because then when it gets a task, it can try to use the excess
                    we'll see

                    this means client knows it failed immediately, effectively gets a free retry
                """
                self.c_unused += 1
                self.c_in_use -= 1
                self.dropped_tasks += 1
                if self.state.config.record_cores_at_drops:
                    self.cores_at_drops.append([self.state.timer.get_time(), len(self.state.available_queues)])
                # breakwater = self.state.breakwater_server
                # print("dumping info for debugging")
                # print("breakwater: credit pool: {0}, credits issued: {1}".format(breakwater.total_credits, breakwater.credits_issued))

            # TODO deregister is off for now
            # may have just finished our last task
            #if self.current_demand <= 0:
                # self.deregister()
            return True

    def add_credit(self):
        self.c_unused += 1
        # should call spend credits
        return self.spend_credits(from_control_loop=True)
        # TODO is multiple credit spending necessary?
        # clients attempt to spend credits upon a task enqueue or receiving credit
        # should not be in a situation where all possible spending is not performed

    # simplify debugging, don't deregister
    def deregister(self):
        # important that this call to server is first, as it will take back credits the client currently has
        self.state.breakwater_server.client_deregister(self)
        self.registered = False
        self.c_unused = 0


