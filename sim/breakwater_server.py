#!/usr/bin/env python
"""object for instance of the breakwater logic at the server in the breakwater system."""

import random

class BreakwaterServer:

    def __init__(self, RTT, ALPHA, BETA, TARGET_DELAY, MAX_CREDITS, state):
        self.state = state
        self.RTT = RTT
        self.target_delay = TARGET_DELAY
        if self.state.config.initial_credits:
            self.total_credits = 25 + int(self.state.config.RTT / 5000) * 150 + int(self.target_delay / 100)
            self.credits_issued = 25 + int(self.state.config.RTT / 5000) * 150 + int(self.target_delay / 100)
        else:
            self.total_credits = 50
            self.credits_issued = 0
        # this will get updated by register
        self.num_clients = 0
        # update clients to be indices, not actual clients, allowing clients to be identified
        self.available_client_ids = []
        self.AGGRESSIVENESS_ALPHA = ALPHA
        self.BETA = BETA
        self.overcommitment_credits = 0
        self.max_delay = 0

        self.credit_pool_records = []
        if self.state.config.initial_credits:
            # TODO 150 is an estimate, should be tested more/calculated better
            self.max_credits = 25 + int(self.state.config.RTT / 5000) * 150 + int(self.target_delay / 100) + 150
        else:
            self.max_credits = MAX_CREDITS

        # TODO debugging
        self.debug_records = []

    def control_loop(self, max_delay=0):
        self.max_delay = max_delay
        # total credit pool
        uppercase_alpha = max(int(self.AGGRESSIVENESS_ALPHA * self.num_clients), 1)

        if max_delay < self.target_delay:
            self.total_credits += uppercase_alpha
            if self.total_credits > self.max_credits:
                self.total_credits = self.max_credits
        else:
            reduction = max(1.0 - self.BETA*((max_delay - self.target_delay)/self.target_delay), 0.5)
            self.total_credits = int(self.total_credits * reduction)

        credits_to_send = self.total_credits - self.credits_issued
        # overcommitment seems to allow massive amounts of credits to build up at client
        self.overcommitment_credits = max(int(credits_to_send / self.num_clients), 1)
        
        # TODO debugging on single client, needs to be adjusted to multiple clients
        # i think this every rtt could be considered "explicit" as needed
        if self.num_clients > 0:
            #self.send_credits(int(credits_to_send))
            # self.state.all_clients[0].dropped_credits = 0
            self.lazy_distribution(0)
        # update: credits will now be sent upon task completion to better emulate
        # how breakwater was actually implemented
        
        if self.state.config.record_credit_pool:
            self.credit_pool_records.append([self.state.timer.get_time(), self.total_credits, self.credits_issued,
                                             self.overcommitment_credits])

    def lazy_distribution(self, client_id):
        """
            issue
            if demand is sky high, won't a single client eat up all available credits?
            how does this ever become fair?
            Won't that single client then also have more opportunities (more responses to task
            completions) to get more credits and have a feedback loop?
        """
        client = self.state.all_clients[client_id]
        available_credits = self.total_credits - self.credits_issued
        # Cx_new = 0
        Cx = client.window
        if available_credits > 0:
            Cx_new = min(client.current_demand + self.overcommitment_credits,
                         Cx + available_credits)

        elif available_credits < 0:
            # grab calculation from paper
            # demand + overcommitment is at least 1 (with 0 demand)
            # what if client is already at 0 credits?
            # num pending?
            Cx_new = min(client.current_demand + self.overcommitment_credits,
                         Cx - 1)
        else:
            # no credit updates needed
            # TODO should client control loop happen here?
            return
        # possible for both situations to result in adding or subtracting credits, depending on
        # demand/pool?
        Cx_new = max(0, Cx_new)
        diff = Cx_new - Cx
        self.credits_issued += diff
        # TODO debugging
        if diff != 0:
            debug = [self.state.timer.get_time(), self.total_credits, diff, Cx_new, Cx, client.dropped_credits,
                     client.current_demand, len(client.queue), client_id]
            self.debug_records.append(debug)

        # update window, and run client control loop
        # TODO is any of this necessary if diff == 0?
        # i.e. should client control loop occur even with no window change?
        # it could still have a shift in credits in use, but is this giving it a
        # chance to spend that it shouldn't have?
        client.window = Cx_new
        client.client_control_loop(from_server=True)

    def client_register(self, client):
        self.available_client_ids.append(client.id)
        # TODO should this still happen if we are overloaded?
        # TODO remove this when done with client initial credits
        if not self.state.config.initial_credits:
            self.credits_issued += 1
            # now, client should be allowed to spend this credit
            client.window = 1
        self.num_clients += 1
        client.client_control_loop()

    def client_deregister(self, client):
        # credits yielded by client
        # should this just be window?
        self.credits_issued -= client.window

        self.available_client_ids.remove(client.id)
        self.num_clients -= 1



