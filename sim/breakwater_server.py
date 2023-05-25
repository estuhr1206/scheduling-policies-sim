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
            # self.credits_issued = 25 + int(self.state.config.RTT / 5000) * 150 + int(self.target_delay / 100)
        else:
            self.total_credits = self.state.config.SERVER_INITIAL_CREDITS
        self.credits_issued = 0
        # this will get updated by register
        self.num_clients = 0
        # update clients to be indices, not actual clients, allowing clients to be identified
        self.available_client_ids = []
        self.AGGRESSIVENESS_ALPHA = ALPHA
        self.BETA = BETA
        self.overcommitment_credits = 1
        self.max_delay = 0

        self.ramp_alpha_records = []

        if self.state.config.zero_initial_cores:
            self.prev_cores = 0
        else:
            self.prev_cores = self.state.config.num_threads

        self.credit_pool_records = []
        if self.state.config.variable_max_credits:
            # TODO 150 is an estimate, should be tested more/calculated better
            self.max_credits = 25 + int(self.state.config.RTT / 5000) * 150 + int(self.target_delay / 100) + 150
        else:
            self.max_credits = MAX_CREDITS

        if self.state.config.variable_min_credits:
            # TODO didn't see a good pattern in the data yet
            self.min_credits = max(self.state.config.MIN_CREDITS, int(self.state.config.RTT / 5000) * 19)
        else:
            self.min_credits = self.state.config.MIN_CREDITS

        # TODO debugging
        self.debug_records = []

    def control_loop(self, max_delay=0):
        self.max_delay = max_delay
        # total credit pool
        # This only applies for multi client scenarios
        uppercase_alpha = max(int(self.AGGRESSIVENESS_ALPHA * self.num_clients), 1)

        if self.state.config.ramp_alpha:
            num_curr_cores = self.state.config.num_threads - len(self.state.parked_threads)
            allocated_during_RTT = num_curr_cores - self.prev_cores
            self.prev_cores = num_curr_cores
            # calculated based on 5 us baseline, 8 credits per core, increasing by 5 every additional 5 us RTT
            # TODO would also vary based on target delay, but needs more testing
            per_core_increase = self.state.config.PER_CORE_ALPHA_INCREASE + ((1-int(self.state.config.RTT / 5000)) * 5)
            if allocated_during_RTT > 0:
                # TODO probably a better calculation approach when number of clients is a factor in alpha
                uppercase_alpha += int(per_core_increase * allocated_during_RTT)
                self.ramp_alpha_records.append([self.state.timer.get_time(), int(per_core_increase*allocated_during_RTT),
                                                self.total_credits, allocated_during_RTT])

        if max_delay < self.target_delay:
            self.total_credits += uppercase_alpha
            if self.total_credits > self.max_credits:
                self.total_credits = self.max_credits
        else:
            reduction = max(1.0 - self.BETA*((max_delay - self.target_delay)/self.target_delay), 0.5)
            self.total_credits = int(self.total_credits * reduction)
            self.total_credits = max(self.total_credits, self.min_credits)

        # TODO debugging on single client, needs to be adjusted to multiple clients
        # TODO Technically not needed, lazy dist would be called on completions
        # also a bit dangerous, isn't delayed by an RTT? Can remove later, need to test incrementally
        # if self.num_clients > 0:
        #     self.lazy_distribution(0)

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
        self.overcommitment_credits = max(int(available_credits / self.num_clients), 1)
        # Cx_new = 0
        Cx = client.window
        # here, demand doesn't go down until responses from success/failure are received
        # with instant credit communication, this is effectively the same as num_pending
        if available_credits > 0:
            Cx_new = min(client.current_demand + self.overcommitment_credits,
                         Cx + available_credits)

        elif available_credits < 0:
            # grab calculation from paper
            # demand + overcommitment is at least 1 (with 0 demand)
            # what if client is already at 0 credits?
            Cx_new = min(client.current_demand + self.overcommitment_credits,
                         Cx - 1)
        else:
            # no credit updates needed
            # TODO should client control loop happen here?
            client.client_control_loop(from_server=True)
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
        self.credits_issued += 1
        # now, client should be allowed to spend this credit
        client.window = 1
        self.num_clients += 1
        # first task comes in with register request
        client.spend_credits()
        # setting OC for lazy dist call
        self.overcommitment_credits = max(int((self.total_credits - self.credits_issued) / self.num_clients), 1)
        self.lazy_distribution(client.id)
        # TODO not needed if call is always present in lazy distribution
        #  extra call, client should be able to do something no matter what
        client.client_control_loop()

    def client_deregister(self, client):
        # credits yielded by client
        # TODO should this just be window?
        self.credits_issued -= client.window

        self.available_client_ids.remove(client.id)
        self.num_clients -= 1



