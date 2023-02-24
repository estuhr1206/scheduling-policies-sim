#!/usr/bin/env python
"""client object for instances of clients in the breakwater system."""

import math
from collections import deque
import random

# clients are initialized in simulation_state.py, (similar to items like the sim_queues)
# list of them can be accessed in main simulation, from sim.state


class BreakwaterClient:

    def __init__(self, state):
        # Where tasks from task creation are placed once they have "arrived"
        self.queue = deque()
        # credits are incremented by server, decremented(used) by client. used as Cx from paper calculations
        self.credits = 0
        # equivalent to number of requests in queue
        self.current_demand = 0
        self.registered = False
        self.state = state
        self.dropped_tasks = 0
        self.total_tasks = 0

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
        if self.credits > 0:
            self.spend_credits()
        elif self.credits < 0:
            # print out that something is wrong
            raise ValueError("error, credits < 0")

    # can instead call the server's register function
    # def register_with_server(self):
    #     pass

    def spend_credits(self):

        # upon no demand
        if self.current_demand <= 0:
            # TODO do nothing, don't deregister for debugging
            # self.deregister()
            # if < 0, something is wrong.
            if self.current_demand < 0:
                raise ValueError('error, demand was below 0')
        else:
            # aqm can happen here, simply don't enqueue it at a core if delay is high
            self.state.breakwater_server.credits_issued -= 1
            self.credits -= 1
            # TODO drop if SLO exceeded
            current_task = self.queue.popleft()
            self.current_demand -= 1

            # check for aqm, if aqm, add some stat for request got dropped
            # breakwater paper: "AQM threshold to 2 · dt (e.g., dt = 80 μs and AQM threshold = 160 μs)"
            if self.state.breakwater_server.max_delay <= 2 * self.state.config.BREAKWATER_TARGET_DELAY:
                # need to override arrival time for core usage
                # this is ok, because the arrival time usage for enqueuing at clients occurs before this
                # override here
                current_task.arrival_time = self.state.timer.get_time()
                # enqueue at core
                chosen_queue = random.choice(self.state.available_queues)
                self.state.queues[chosen_queue].enqueue(current_task, set_original=True)
            else:
                # shouldn't be dropped if load is low (aka the 50%)
                # TODO can be put back in, will cause issues for varycores run
                self.dropped_tasks += 1
                # breakwater = self.state.breakwater_server
                # print("dumping info for debugging")
                # print("breakwater: credit pool: {0}, credits issued: {1}".format(breakwater.total_credits, breakwater.credits_issued))

                # print("queue lengths and delays")
                # for q in self.state.queues:
                #     print(len(q.queue), q.current_delay())
                # raise ValueError('error, tasked dropped (disregard if operating at/near capacity), delay was {0}, client demand: {1}, client credits: {2}'
                #                  .format(breakwater.max_delay, self.current_demand, self.credits))

            # may have just finished our last task
            #if self.current_demand <= 0:
                # self.deregister()

    def add_credit(self):
        self.credits += 1
        # should call spend credits
        self.spend_credits()
        # TODO is multiple credit spending necessary?
        # clients attempt to spend credits upon a task enqueue or receiving credit
        # should not be in a situation where all possible spending is not performed

    # simplify debugging, don't deregister
    def deregister(self):
        # important that this call to server is first, as it will take back credits the client currently has
        self.state.breakwater_server.client_deregister(self)
        self.registered = False
        self.credits = 0


